#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريپت تشغيل سريع لتطبيق إدارة MikroTik
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """فحص إصدار Python"""
    if sys.version_info < (3, 7):
        print("❌ يتطلب Python 3.7 أو أحدث")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]}")

def check_requirements():
    """فحص وتثبيت المتطلبات"""
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ ملف requirements.txt غير موجود")
        sys.exit(1)
    
    print("📦 فحص المتطلبات...")
    try:
        # محاولة استيراد المكتبات الأساسية
        import librouteros
        import flask
        print("✅ جميع المتطلبات متوفرة")
    except ImportError as e:
        print(f"⚠️  مكتبة مفقودة: {e.name}")
        print("🔧 تثبيت المتطلبات...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ تم تثبيت المتطلبات")

def check_env_file():
    """فحص ملف البيئة"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  ملف .env غير موجود")
        print("📝 إنشاء ملف .env من المثال...")
        
        example_file = Path(".env.example")
        if example_file.exists():
            import shutil
            shutil.copy(".env.example", ".env")
            print("✅ تم إنشاء ملف .env")
            print("🔧 عدل ملف .env بإعداداتك الصحيحة")
        else:
            print("❌ ملف .env.example غير موجود")
    else:
        print("✅ ملف .env موجود")

def test_mikrotik_connection():
    """اختبار الاتصال بـ MikroTik"""
    print("\n🔌 اختبار الاتصال بـ MikroTik...")
    
    try:
        from mikrotik_manager import MikroTikManager
        from dotenv import load_dotenv
        
        load_dotenv()
        
        host = os.getenv('MIKROTIK_HOST', '89.189.68.60')
        port = int(os.getenv('MIKROTIK_PORT', '2080'))
        username = os.getenv('MIKROTIK_USERNAME', 'admin')
        password = os.getenv('MIKROTIK_PASSWORD', 'khalid')
        
        print(f"📡 محاولة الاتصال بـ {host}:{port}")
        
        mt = MikroTikManager(host, username, password, port, timeout=5)
        if mt.connect():
            print("✅ تم الاتصال بنجاح!")
            
            # جلب معلومات أساسية
            system_info = mt.get_system_info()
            if system_info:
                print(f"🖥️  الجهاز: {system_info.get('board-name', 'غير معروف')}")
                print(f"📊 RouterOS: {system_info.get('version', 'غير معروف')}")
            
            mt.disconnect()
            return True
        else:
            print("❌ فشل في الاتصال")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {e}")
        return False

def show_help():
    """عرض المساعدة"""
    print("""
🔧 مساعدة استكشاف الأخطاء:

1. تأكد من تفعيل API في MikroTik:
   - افتح Winbox
   - اذهب إلى IP → Services
   - فعل خدمة "api" على المنفذ 2080

2. تأكد من إعدادات Firewall:
   - IP → Firewall → Filter Rules
   - تأكد من السماح للمنفذ 2080

3. إذا كان الخادم خلف NAT:
   - أضف Port Forwarding للمنفذ 2080
   - IP → Firewall → NAT

4. تحقق من ملف .env:
   - MIKROTIK_HOST: عنوان IP الصحيح
   - MIKROTIK_PORT: 2080 (منفذ API وليس Winbox)
   - MIKROTIK_USERNAME & MIKROTIK_PASSWORD: بيانات صحيحة
""")

def main():
    """الدالة الرئيسية"""
    print("🚀 تطبيق إدارة MikroTik")
    print("=" * 40)
    
    # فحص المتطلبات
    check_python_version()
    check_requirements()
    check_env_file()
    
    # اختبار الاتصال
    connection_ok = test_mikrotik_connection()
    
    if not connection_ok:
        print("\n⚠️  تحذير: فشل في الاتصال بـ MikroTik")
        print("💡 يمكنك تشغيل التطبيق ومحاولة الاتصال من الواجهة")
        
        choice = input("\nهل تريد عرض مساعدة استكشاف الأخطاء؟ (y/n): ")
        if choice.lower() in ['y', 'yes', 'نعم']:
            show_help()
    
    print("\n🌐 تشغيل التطبيق...")
    print("📱 ستفتح الواجهة على: http://localhost:5002")
    print("⏹️  اضغط Ctrl+C لإيقاف التطبيق")
    print("=" * 40)
    
    # تشغيل التطبيق
    try:
        from app import app
        app.run(debug=True, port=5002, host='0.0.0.0')
    except KeyboardInterrupt:
        print("\n👋 تم إيقاف التطبيق")
    except Exception as e:
        print(f"\n❌ خطأ في تشغيل التطبيق: {e}")

if __name__ == "__main__":
    main()
