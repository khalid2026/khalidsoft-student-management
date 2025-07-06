#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أداة تشخيص الاتصال بسيرفر ميكروتك
MikroTik Connection Diagnostic Tool
"""

import socket
import time
import sys
from typing import Dict, Any

def test_basic_connectivity(host: str, port: int, timeout: int = 5) -> Dict[str, Any]:
    """اختبار الاتصال الأساسي بالسيرفر"""
    result = {
        'success': False,
        'message': '',
        'details': {}
    }
    
    try:
        print(f"🔍 اختبار الاتصال الأساسي بـ {host}:{port}")
        
        # اختبار ping أولاً
        import subprocess
        ping_result = subprocess.run(['ping', '-c', '3', host], 
                                   capture_output=True, text=True, timeout=10)
        
        if ping_result.returncode == 0:
            print("✅ Ping ناجح - السيرفر متاح")
            result['details']['ping'] = 'success'
        else:
            print("❌ Ping فاشل - السيرفر غير متاح")
            result['details']['ping'] = 'failed'
            result['message'] = 'السيرفر غير متاح عبر الشبكة'
            return result
            
    except Exception as e:
        print(f"⚠️ لا يمكن اختبار Ping: {e}")
        result['details']['ping'] = 'unknown'
    
    try:
        # اختبار الاتصال بالمنفذ
        print(f"🔌 اختبار الاتصال بالمنفذ {port}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        start_time = time.time()
        connection_result = sock.connect_ex((host, port))
        end_time = time.time()
        
        sock.close()
        
        if connection_result == 0:
            print(f"✅ المنفذ {port} مفتوح ومتاح")
            print(f"⏱️ وقت الاستجابة: {(end_time - start_time)*1000:.2f} ms")
            result['success'] = True
            result['message'] = f'المنفذ {port} متاح'
            result['details']['port'] = 'open'
            result['details']['response_time'] = f"{(end_time - start_time)*1000:.2f} ms"
        else:
            print(f"❌ المنفذ {port} مغلق أو محجوب")
            result['message'] = f'المنفذ {port} غير متاح'
            result['details']['port'] = 'closed'
            
    except socket.timeout:
        print(f"⏰ انتهت مهلة الاتصال بالمنفذ {port}")
        result['message'] = 'انتهت مهلة الاتصال'
        result['details']['port'] = 'timeout'
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {e}")
        result['message'] = f'خطأ في الاتصال: {e}'
        result['details']['port'] = 'error'
    
    return result

def test_alternative_ports(host: str) -> Dict[str, Any]:
    """اختبار منافذ بديلة شائعة لميكروتك"""
    common_ports = [8728, 8729, 2080, 80, 443, 8080, 8291]
    results = {}
    
    print("🔍 اختبار المنافذ الشائعة لميكروتك:")
    
    for port in common_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print(f"✅ المنفذ {port} مفتوح")
                results[port] = 'open'
            else:
                print(f"❌ المنفذ {port} مغلق")
                results[port] = 'closed'
                
        except Exception as e:
            print(f"⚠️ خطأ في اختبار المنفذ {port}: {e}")
            results[port] = 'error'
    
    return results

def main():
    """الوظيفة الرئيسية"""
    print("=" * 60)
    print("🚀 أداة تشخيص الاتصال بسيرفر ميكروتك")
    print("=" * 60)
    
    # إعدادات الاتصال
    host = "89.189.68.60"
    port = 2080
    username = "admin"
    password = "khalid"
    
    print(f"📋 إعدادات الاتصال:")
    print(f"   🌐 العنوان: {host}")
    print(f"   🔌 المنفذ: {port}")
    print(f"   👤 المستخدم: {username}")
    print(f"   🔑 كلمة المرور: {'*' * len(password)}")
    print()
    
    # اختبار الاتصال الأساسي
    basic_test = test_basic_connectivity(host, port)
    print()
    
    # اختبار المنافذ البديلة
    print("🔍 اختبار المنافذ البديلة:")
    alternative_ports = test_alternative_ports(host)
    print()
    
    # ملخص النتائج
    print("=" * 60)
    print("📊 ملخص النتائج:")
    print("=" * 60)
    
    if basic_test['success']:
        print("✅ الاتصال الأساسي: ناجح")
        print("🎉 المنفذ 2080 متاح!")
    else:
        print("❌ الاتصال الأساسي: فاشل")
        print("💡 تحقق من:")
        print("   - إعدادات الشبكة")
        print("   - إعدادات الجدار الناري")
        print("   - صحة عنوان IP")
        print("   - تفعيل خدمة API على ميكروتك")
    
    # عرض المنافذ المفتوحة
    open_ports = [port for port, status in alternative_ports.items() if status == 'open']
    if open_ports:
        print(f"🔓 المنافذ المفتوحة: {', '.join(map(str, open_ports))}")
        if 8728 in open_ports:
            print("💡 المنفذ 8728 مفتوح - هذا هو المنفذ الافتراضي لـ API")
        if 8291 in open_ports:
            print("💡 المنفذ 8291 مفتوح - هذا هو منفذ Winbox")
    else:
        print("🔒 لا توجد منافذ مفتوحة من المنافذ المختبرة")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
