import requests
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Door, Order

@login_required
def send_telegram_order(request, door_id):
    if request.method == "POST":
        door = get_object_or_404(Door, id=door_id)
        phone = request.POST.get('phone')
        
        TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  
        CHAT_ID = "YOUR_CHAT_ID"        

        text = f"🔔 YANGI BUYURTMA\nEshik: {door.name}\nNarxi: {door.price} UZS\nMijoz: {phone}"

        try:
            r = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                data={"chat_id": CHAT_ID, "text": text},
                timeout=10
            )
            # Agar yuborish muvaffaqiyatli bo‘lsa
            if r.status_code == 200:
                Order.objects.create(door=door, phone=phone)
                return JsonResponse({"status":"ok"})
            else:
                return JsonResponse({"status":"error","message":"Telegramga yuborib bo'lmadi"})
        except Exception as e:
            return JsonResponse({"status":"error","message":str(e)})
    
    return JsonResponse({"status":"error","message":"Invalid request"})