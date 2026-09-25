import re

import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login,  authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.http import require_GET
from .models import Door

BOT_SUGGESTIONS = [
    "Premium eshiklar",
    "Standart eshiklar",
    "2 mln gacha eshik",
    "Kontaktlar",
]

BOT_STOP_WORDS = {
    "eshik", "eshiklar", "kerak", "bormi", "haqida", "qanday", "menga",
    "bor", "kerakmi", "uchun", "qaysi", "bilan", "bot", "sayt", "saytimga",
    "iltimos", "salom", "assalomu", "alaykum", "narx", "narcha", "necha",
}


def _format_price(value):
    return f"{value:,}".replace(",", " ")


def _format_door_list(doors):
    lines = []
    for index, door in enumerate(doors, start=1):
        lines.append(
            f"{index}. {door.name} | {door.brand} | {_format_price(door.price)} UZS"
        )
    return "\n".join(lines)


def _extract_budget(message):
    match = re.search(r"(\d[\d\s]*(?:[.,]\d+)?)\s*(mln|million|ming|k)?", message.lower())
    if not match:
        return None

    raw_amount = match.group(1).replace(" ", "").replace(",", ".")
    amount = float(raw_amount)
    suffix = match.group(2)

    if suffix in {"mln", "million"}:
        amount *= 1_000_000
    elif suffix in {"ming", "k"}:
        amount *= 1_000

    return int(amount)


def _find_matching_doors(message):
    direct_matches = Door.objects.filter(
        Q(name__icontains=message) |
        Q(brand__icontains=message) |
        Q(coating__icontains=message) |
        Q(structure__icontains=message)
    ).distinct()
    if direct_matches.exists():
        return direct_matches.order_by("price")[:3]

    tokens = [
        token for token in re.findall(r"[a-z0-9']+", message.lower())
        if len(token) >= 3 and token not in BOT_STOP_WORDS
    ]
    if not tokens:
        return Door.objects.none()

    query = Q()
    for token in tokens:
        query |= (
            Q(name__icontains=token) |
            Q(brand__icontains=token) |
            Q(category__icontains=token) |
            Q(coating__icontains=token) |
            Q(structure__icontains=token)
        )

    return Door.objects.filter(query).distinct().order_by("price")[:3]


def _chatbot_reply(message):
    normalized = message.lower().strip()
    tokens = set(re.findall(r"[a-z0-9']+", normalized))
    total_doors = Door.objects.count()

    if not normalized:
        return (
            f"Salom. Men SFDOORS yordamchi botiman. Hozir katalogda {total_doors} ta eshik bor. "
            "Sizga kategoriya, narx, buyurtma yoki kontaktlar bo'yicha yordam bera olaman.",
            BOT_SUGGESTIONS,
        )

    if tokens.intersection({"salom", "assalomu", "alaykum", "hello", "hi"}):
        return (
            "Salom. Sizga Premium yoki Standart eshiklarni topib beraman, narx bo'yicha saralayman "
            "va buyurtma berish tartibini tushuntiraman.",
            BOT_SUGGESTIONS,
        )

    if any(word in normalized for word in ["kontakt", "aloqa", "telefon", "raqam", "manzil", "address", "ish vaqti"]):
        return (
            "Bog'lanish uchun saytda ko'rsatilgan raqamlar:\n"
            "1. +998 94 637 69 60\n"
            "2. +998 93 570 27 64\n"
            "Manzil: Toshkent, Sebzor 8-uy\n"
            "Ish vaqti: har kuni 09:00 - 20:00",
            ["Buyurtma qanday beriladi?", "Premium eshiklar", "Standart eshiklar"],
        )

    if any(word in normalized for word in ["buyurtma", "zakaz", "sotib", "olmoqchi", "olish"]):
        return (
            "Buyurtma berish uchun katalogdan eshikni oching, telefon raqamingizni kiriting va "
            "\"Telegram orqali buyurtma\" tugmasini bosing. Agar xohlasangiz, men avval sizga mos "
            "modelni ham tavsiya qilaman.",
            ["2 mln gacha eshik", "Premium eshiklar", "Kontaktlar"],
        )

    for category in ["premium", "standart"]:
        if category in normalized:
            category_name = category.capitalize()
            doors = Door.objects.filter(category__iexact=category_name).order_by("price")[:3]
            count = Door.objects.filter(category__iexact=category_name).count()
            if not doors:
                return (
                    f"Hozircha {category_name} kategoriyasida mahsulot topilmadi.",
                    BOT_SUGGESTIONS,
                )
            return (
                f"{category_name} kategoriyasida {count} ta eshik bor. Tavsiya qilaman:\n"
                f"{_format_door_list(doors)}",
                ["Narxi arzon eshiklar", "Kontaktlar", "Buyurtma qanday beriladi?"],
            )

    budget = _extract_budget(normalized)
    if budget and any(word in normalized for word in ["narx", "gacha", "budjet", "budget", "sum", "so'm", "uzs", "mln", "million"]):
        doors = Door.objects.filter(price__lte=budget).order_by("price")[:3]
        if doors:
            return (
                f"{_format_price(budget)} UZS gacha quyidagi variantlar mos keladi:\n"
                f"{_format_door_list(doors)}",
                ["Yana arzonroq variantlar", "Premium eshiklar", "Kontaktlar"],
            )
        return (
            f"{_format_price(budget)} UZS gacha mos eshik topilmadi. Budjetni biroz oshirib ko'ring "
            "yoki kategoriya bo'yicha so'rang.",
            ["Standart eshiklar", "Premium eshiklar", "Kontaktlar"],
        )

    if any(word in normalized for word in ["narx", "qancha", "necha pul", "eng arzon", "arzon"]):
        cheapest = Door.objects.order_by("price").first()
        priciest = Door.objects.order_by("-price").first()
        if cheapest and priciest:
            return (
                f"Katalogdagi narx oralig'i {_format_price(cheapest.price)} UZS dan "
                f"{_format_price(priciest.price)} UZS gacha.\n"
                f"Eng arzon variant: {cheapest.name} ({cheapest.brand})\n"
                f"Premium tomondan ko'rish uchun ham tavsiya bera olaman.",
                ["2 mln gacha eshik", "Premium eshiklar", "Standart eshiklar"],
            )

    matching_doors = _find_matching_doors(normalized)
    if matching_doors:
        return (
            "Sizning so'rovingizga yaqin eshiklar:\n"
            f"{_format_door_list(matching_doors)}",
            ["Narxlari qanday?", "Buyurtma qanday beriladi?", "Kontaktlar"],
        )

    return (
        "Savolingizni tushundim, lekin aniqroq yozsangiz yaxshiroq tavsiya beraman. "
        "Masalan: \"Premium eshiklar\", \"2 mln gacha eshik\" yoki \"Kontaktlar\".",
        BOT_SUGGESTIONS,
    )

def home(request):
    # Hamma eshiklarni olish
    doors_list = Door.objects.all().order_by("-id")
    

    query = request.GET.get("q")
    if query:
        doors_list = doors_list.filter(
            Q(name__icontains=query) | Q(brand__icontains=query)
        )
    

    cat = request.GET.get("category")
    if cat and cat != 'Barchasi':
        doors_list = doors_list.filter(category=cat)

    paginator = Paginator(doors_list, 8)
    page_number = request.GET.get('page')
    doors = paginator.get_page(page_number)
    
    
    return render(request, "dooors/home.html", {
        "doors": doors, 
        "query": query,
        "current_category": cat
    })

def about(request):
    return render(request, "dooors/about.html")

def contact(request):
    return render(request, "dooors/contact.html")


@require_GET
def chatbot_view(request):
    message = request.GET.get("message", "")
    reply, suggestions = _chatbot_reply(message)
    return JsonResponse({
        "reply": reply,
        "suggestions": suggestions,
    })

def send_telegram_order(request, door_id):
    if request.method == "POST":
        door = get_object_or_404(Door, id=door_id)
        phone = request.POST.get('phone')
        
        TOKEN = "7867389445:AAHlH-jXNfO0-R0A5q9H7u6Fq8p9A"
        CHAT_ID = "6155605555"
        text = f"🔔 YANGI BUYURTMA\n\n🚪 Eshik: {door.name}\n💰 Narxi: {door.price} UZS\n📞 Mijoz: {phone}"
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        
        try:
            requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=10)
            return JsonResponse({"status": "ok"})
        except Exception:
            return JsonResponse({"status": "error"})

def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "dooors/register.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("dashboard" if user.is_staff else "home")
    else:
        form = AuthenticationForm()
    return render(request, "dooors/login.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect("home")

@staff_member_required
def dashboard(request):
    context = {
        "doors_count": Door.objects.count(),
    }
    return render(request, "dooors/dashboard.html", context)

@staff_member_required
def my_doors(request):

    doors = Door.objects.all().order_by("-id")
    return render(request, "dooors/my_doors.html", {"doors": doors})

@staff_member_required
def add_door(request):
    if request.method == "POST":
        
        name = request.POST.get('name')
        brand = request.POST.get('brand')
        price = request.POST.get('price')
        category = request.POST.get('category')
        coating = request.POST.get('coating')
        structure = request.POST.get('structure')
        description = request.POST.get('description', '')
        image = request.FILES.get('image')

        if name and price and image:
            Door.objects.create(
                name=name, brand=brand, price=price,
                category=category, coating=coating,
                structure=structure, description=description,
                image=image
            )
            messages.success(request, "Eshik muvaffaqiyatli qo'shildi!")
            return redirect('my_doors')
            
    return render(request, "dooors/add.html", {"edit_mode": False})

@staff_member_required
def edit_door(request, pk):
    door = get_object_or_404(Door, pk=pk)
    if request.method == "POST":
        door.name = request.POST.get('name')
        door.brand = request.POST.get('brand')
        door.price = request.POST.get('price')
        door.category = request.POST.get('category')
        door.coating = request.POST.get('coating')
        door.structure = request.POST.get('structure')
        door.description = request.POST.get('description')
        
        
        new_image = request.FILES.get('image')
        if new_image:
            door.image = new_image
            
        door.save()
        messages.info(request, "Eshik ma'lumotlari yangilandi.")
        return redirect('my_doors')
    
    return render(request, "dooors/add.html", {"door": door, "edit_mode": True})

@staff_member_required
def delete_door(request, pk):
    door = get_object_or_404(Door, pk=pk)
    if request.method == "POST":
        door.delete()
        messages.warning(request, "Eshik o'chirib tashlandi.")
        return redirect('my_doors')
    return render(request, "dooors/delete_confirm.html", {"door": door})
