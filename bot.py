import os
import logging
from pyrogram import Client, filters
from pyrogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton
)
from motor.motor_asyncio import AsyncIOMotorClient

# إعدادات التسجيل لتتبع الحالة
logging.basicConfig(level=logging.INFO)

# مفاتيح البوت والربط التي تم جمعها
API_ID = 37213380  # الـ API ID الخاص بك
API_HASH = "910bef2d65e7fd2e14ac6221f80c46d3"  # الـ API Hash الخاص بك
BOT_TOKEN = "8230997368:AAFs6nOUYSe7wyFjBQ0-SL8OEuhfi_57Q4w"  # توكن البوت
MONGO_URI = "mongodb+srv://kmskms01090205243_db_user:كلمة_المرور_هنا@bot.dnzzbjt.mongodb.net/?compressors=zlib"  # رابط قاعدة البيانات بعد وضع الباسورد

# الاتصال بقاعدة البيانات السحابية (MongoDB)
db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client["secure_vault_bot"]
users_col = db["users"]
media_col = db["media_files"]

# تشغيل عميل التيليجرام بوست
app = Client(
    "secure_vault_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# 1. أمر البداية والتحقق من الأمان
@app.on_message(filters.command("start"))
async def start_command(client, message):
    user_id = message.from_user.id
    user_data = await users_col.find_one({"user_id": user_id})
    
    if not user_data or "phone_number" not in user_data:
        # زرار مشاركة رقم الهاتف للأمان والتحقق
        phone_button = ReplyKeyboardMarkup(
            [[KeyboardButton("📱 تحقق من رقم الهاتف للأمان", request_contact=True)]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
        await message.reply(
            "مرحباً بك في خزنتك السحابية الآمنة (الصندوق الأسود) 🔒\n\nلضمان حماية صورك وفيديوهاتك واسترجاعها في أي وقت حتى لو تم حذف البوت، يرجى تأكيد رقم هاتفك أولاً:",
            reply_markup=phone_button
        )
    else:
        await message.reply(
            f"أهلاً بك مجدداً يا {message.from_user.first_name} 🛡️\n\nحسابك مؤمن برقم الهاتف ({user_data['phone_number']}). الخزنة جاهزة؛ يمكنك إرسال أي صور، فيديوهات، أو ملفات لحفظها للأبد."
        )

# 2. استقبال وحفظ رقم الهاتف بعد التحقق
@app.on_message(filters.contact)
async def save_contact(client, message):
    user_id = message.from_user.id
    phone_number = message.contact.phone_number
    
    # حفظ أو تحديث بيانات المستخدم وقاعدة البيانات
    await users_col.update_one(
        {"user_id": user_id},
        {"$set": {"phone_number": phone_number, "name": message.from_user.first_name}},
        upsert=True
    )
    
    await message.reply(
        "✅ تم التحقق من رقم هاتفك بنجاح وربط الخزنة السحابية برقمك!\nيمكنك الآن إرسال أي صور أو فيديوهات، وسيتم حفظها بشكل دائم وآمن."
    )

# 3. استقبال وحفظ الصور والفيديوهات والملفات في MongoDB
@app.on_message(filters.photo | filters.video | filters.document)
async def save_media(client, message):
    user_id = message.from_user.id
    user_data = await users_col.find_one({"user_id": user_id})
    
    # التأكد أن المستخدم أكد رقمه للأمان أولاً
    if not user_data or "phone_number" not in user_data:
        await message.reply("⚠️ تنبيه: يجب التحقق من رقم الهاتف أولاً قبل رفع الملفات للأمان. أرسل /start للبدء.")
        return
    
    # تحديد نوع الملف ومعرفه الفريد في تيليجرام (File ID)
    file_id = None
    file_type = ""
    if message.photo:
        file_id = message.photo.file_id
        file_type = "photo"
    elif message.video:
        file_id = message.video.file_id
        file_type = "video"
    elif message.document:
        file_id = message.document.file_id
        file_type="document"
        
    # تخزين مرجع الملف في قاعدة البيانات مرتبط برقم الهاتف ومعرف المستخدم
    await media_col.insert_one({
        "user_id": user_id,
        "phone_number": user_data["phone_number"],
        "file_id": file_id,
        "file_type": file_type
    })
    
    await message.reply("💾 تم حفظ الملف في خزنتك السحابية بنجاح ولن يضيع أبداً حتى لو تم إعادة تعيين البوت!")

# تشغيل البوت
if __name__ == "__main__":
    print("Secure Vault Bot is running...")
    app.run()
