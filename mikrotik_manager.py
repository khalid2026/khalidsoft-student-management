#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أداة إدارة MikroTik RouterOS
مطور بواسطة Augment Agent
"""

import librouteros
import socket
import time
from typing import Dict, List, Optional, Any
import logging

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MikroTikManager:
    """فئة لإدارة أجهزة MikroTik RouterOS عبر API"""
    
    def __init__(self, host: str, username: str, password: str, port: int = 2080, timeout: int = 10):
        """
        إنشاء اتصال جديد بجهاز MikroTik
        
        Args:
            host: عنوان IP للجهاز
            username: اسم المستخدم
            password: كلمة المرور
            port: منفذ API (افتراضي 8728)
            timeout: مهلة الاتصال بالثواني
        """
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout
        self.api = None
        self.connected = False
        
    def connect(self) -> bool:
        """
        الاتصال بجهاز MikroTik

        Returns:
            True إذا نجح الاتصال، False إذا فشل
        """
        try:
            logger.info(f"محاولة الاتصال بـ {self.host}:{self.port}")

            # إنشاء اتصال باستخدام librouteros
            self.api = librouteros.connect(
                host=self.host,
                username=self.username,
                password=self.password,
                port=self.port,
                timeout=self.timeout
            )
            self.connected = True

            logger.info("تم الاتصال بنجاح!")
            return True

        except socket.timeout:
            logger.error("انتهت مهلة الاتصال")
            return False
        except socket.error as e:
            logger.error(f"خطأ في الشبكة: {e}")
            return False
        except Exception as e:
            logger.error(f"خطأ في تسجيل الدخول: {e}")
            return False
    
    def disconnect(self):
        """قطع الاتصال"""
        if self.api:
            try:
                self.api.close()
                self.connected = False
                logger.info("تم قطع الاتصال")
            except:
                pass
    
    def is_connected(self) -> bool:
        """فحص حالة الاتصال"""
        return self.connected and self.api is not None
    
    def execute_command(self, command: str, arguments: Dict[str, Any] = None) -> List[Dict]:
        """
        تنفيذ أمر RouterOS
        
        Args:
            command: الأمر المراد تنفيذه
            arguments: معاملات الأمر
            
        Returns:
            قائمة بالنتائج
        """
        if not self.is_connected():
            if not self.connect():
                raise ConnectionError("فشل في الاتصال بالجهاز")
        
        try:
            if arguments:
                result = list(self.api(cmd=command, **arguments))
            else:
                result = list(self.api(cmd=command))
            return result
        except Exception as e:
            logger.error(f"خطأ في تنفيذ الأمر {command}: {e}")
            raise
    
    def get_system_info(self) -> Dict:
        """الحصول على معلومات النظام"""
        try:
            result = self.execute_command('/system/resource/print')
            if result:
                return result[0]
            return {}
        except Exception as e:
            logger.error(f"خطأ في الحصول على معلومات النظام: {e}")
            return {}
    
    def get_active_users(self) -> List[Dict]:
        """الحصول على قائمة المستخدمين المتصلين"""
        try:
            # المستخدمين النشطين في PPP
            ppp_users = self.execute_command('/ppp/active/print')
            
            # المستخدمين النشطين في Hotspot
            hotspot_users = []
            try:
                hotspot_users = self.execute_command('/ip/hotspot/active/print')
            except:
                pass  # قد لا يكون Hotspot مفعل
            
            # دمج القوائم
            all_users = []
            
            for user in ppp_users:
                all_users.append({
                    'type': 'PPP',
                    'name': user.get('name', 'غير معروف'),
                    'address': user.get('address', 'غير معروف'),
                    'uptime': user.get('uptime', '0'),
                    'service': user.get('service', 'غير معروف')
                })
            
            for user in hotspot_users:
                all_users.append({
                    'type': 'Hotspot',
                    'name': user.get('user', 'غير معروف'),
                    'address': user.get('address', 'غير معروف'),
                    'uptime': user.get('uptime', '0'),
                    'service': 'hotspot'
                })
            
            return all_users
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على المستخدمين: {e}")
            return []
    
    def get_interfaces(self) -> List[Dict]:
        """الحصول على قائمة الواجهات"""
        try:
            interfaces = self.execute_command('/interface/print')
            return [
                {
                    'name': iface.get('name', 'غير معروف'),
                    'type': iface.get('type', 'غير معروف'),
                    'running': iface.get('running', 'false') == 'true',
                    'disabled': iface.get('disabled', 'false') == 'true'
                }
                for iface in interfaces
            ]
        except Exception as e:
            logger.error(f"خطأ في الحصول على الواجهات: {e}")
            return []
    
    def get_ip_addresses(self) -> List[Dict]:
        """الحصول على عناوين IP"""
        try:
            addresses = self.execute_command('/ip/address/print')
            return [
                {
                    'address': addr.get('address', 'غير معروف'),
                    'interface': addr.get('interface', 'غير معروف'),
                    'network': addr.get('network', 'غير معروف'),
                    'disabled': addr.get('disabled', 'false') == 'true'
                }
                for addr in addresses
            ]
        except Exception as e:
            logger.error(f"خطأ في الحصول على عناوين IP: {e}")
            return []

    def disconnect_user(self, user_id: str, user_type: str = 'ppp') -> bool:
        """قطع اتصال مستخدم"""
        try:
            if user_type.lower() == 'ppp':
                command = '/ppp/active/remove'
            elif user_type.lower() == 'hotspot':
                command = '/ip/hotspot/active/remove'
            else:
                logger.error(f"نوع مستخدم غير مدعوم: {user_type}")
                return False

            self.execute_command(command, {'.id': user_id})
            logger.info(f"تم قطع اتصال المستخدم {user_id}")
            return True

        except Exception as e:
            logger.error(f"خطأ في قطع اتصال المستخدم {user_id}: {e}")
            return False

    def get_ppp_secrets(self) -> List[Dict]:
        """الحصول على قائمة مستخدمي PPP"""
        try:
            secrets = self.execute_command('/ppp/secret/print')
            return [
                {
                    'id': secret.get('.id', ''),
                    'name': secret.get('name', 'غير معروف'),
                    'service': secret.get('service', 'غير معروف'),
                    'profile': secret.get('profile', 'غير معروف'),
                    'local_address': secret.get('local-address', ''),
                    'remote_address': secret.get('remote-address', ''),
                    'disabled': secret.get('disabled', 'false') == 'true'
                }
                for secret in secrets
            ]
        except Exception as e:
            logger.error(f"خطأ في الحصول على مستخدمي PPP: {e}")
            return []

    def disable_user(self, user_id: str) -> bool:
        """تعطيل مستخدم PPP"""
        try:
            self.execute_command('/ppp/secret/disable', {'.id': user_id})
            logger.info(f"تم تعطيل المستخدم {user_id}")
            return True
        except Exception as e:
            logger.error(f"خطأ في تعطيل المستخدم {user_id}: {e}")
            return False

    def enable_user(self, user_id: str) -> bool:
        """تفعيل مستخدم PPP"""
        try:
            self.execute_command('/ppp/secret/enable', {'.id': user_id})
            logger.info(f"تم تفعيل المستخدم {user_id}")
            return True
        except Exception as e:
            logger.error(f"خطأ في تفعيل المستخدم {user_id}: {e}")
            return False

    def get_user_traffic(self, username: str) -> Dict:
        """الحصول على إحصائيات حركة البيانات للمستخدم"""
        try:
            # البحث في PPP active
            ppp_active = self.execute_command('/ppp/active/print', {'?name': username})
            if ppp_active:
                user = ppp_active[0]
                return {
                    'bytes_in': user.get('bytes-in', '0'),
                    'bytes_out': user.get('bytes-out', '0'),
                    'packets_in': user.get('packets-in', '0'),
                    'packets_out': user.get('packets-out', '0'),
                    'uptime': user.get('uptime', '0')
                }
            return {}
        except Exception as e:
            logger.error(f"خطأ في الحصول على إحصائيات المستخدم {username}: {e}")
            return {}

    def create_ppp_user(self, username: str, password: str, profile: str = 'default',
                       local_address: str = '', remote_address: str = '',
                       service: str = 'any') -> bool:
        """إنشاء مستخدم PPP جديد"""
        try:
            params = {
                'name': username,
                'password': password,
                'profile': profile,
                'service': service
            }

            if local_address:
                params['local-address'] = local_address
            if remote_address:
                params['remote-address'] = remote_address

            self.execute_command('/ppp/secret/add', params)
            logger.info(f"تم إنشاء المستخدم {username} بنجاح")
            return True

        except Exception as e:
            logger.error(f"خطأ في إنشاء المستخدم {username}: {e}")
            return False

    def delete_ppp_user(self, user_id: str) -> bool:
        """حذف مستخدم PPP"""
        try:
            self.execute_command('/ppp/secret/remove', {'.id': user_id})
            logger.info(f"تم حذف المستخدم {user_id} بنجاح")
            return True
        except Exception as e:
            logger.error(f"خطأ في حذف المستخدم {user_id}: {e}")
            return False

    def update_user_password(self, user_id: str, new_password: str) -> bool:
        """تحديث كلمة مرور المستخدم"""
        try:
            self.execute_command('/ppp/secret/set', {
                '.id': user_id,
                'password': new_password
            })
            logger.info(f"تم تحديث كلمة مرور المستخدم {user_id}")
            return True
        except Exception as e:
            logger.error(f"خطأ في تحديث كلمة مرور المستخدم {user_id}: {e}")
            return False

    def get_ppp_profiles(self) -> List[Dict]:
        """الحصول على قائمة ملفات PPP الشخصية"""
        try:
            profiles = self.execute_command('/ppp/profile/print')
            return [
                {
                    'id': profile.get('.id', ''),
                    'name': profile.get('name', 'غير معروف'),
                    'local_address': profile.get('local-address', ''),
                    'remote_address': profile.get('remote-address', ''),
                    'rate_limit': profile.get('rate-limit', '')
                }
                for profile in profiles
            ]
        except Exception as e:
            logger.error(f"خطأ في الحصول على ملفات PPP: {e}")
            return []

    def create_bulk_users(self, prefix: str = '', count: int = 10, password_length: int = 8,
                         profile: str = 'default', name_type: str = 'prefix',
                         custom_names: List[str] = None) -> List[Dict]:
        """إنشاء عدد كبير من مستخدمي PPP مع دعم الأسماء العربية"""
        import random
        import string

        created_users = []

        # تحديد الأسماء حسب النوع
        if name_type == 'custom' and custom_names:
            usernames = custom_names
            count = len(usernames)
        else:
            usernames = []
            for i in range(1, count + 1):
                username = f"{prefix}{i:03d}"  # مثل: user001, محمد001
                usernames.append(username)

        for username in usernames:
            # توليد كلمة مرور عشوائية
            password = ''.join(random.choices(
                string.ascii_letters + string.digits,
                k=password_length
            ))

            if self.create_ppp_user(username, password, profile):
                created_users.append({
                    'username': username,
                    'password': password,
                    'profile': profile,
                    'type': 'ppp',
                    'status': 'تم الإنشاء'
                })
            else:
                created_users.append({
                    'username': username,
                    'password': password,
                    'profile': profile,
                    'type': 'ppp',
                    'status': 'فشل'
                })

        return created_users

    def get_system_resources(self) -> Dict:
        """الحصول على موارد النظام المفصلة"""
        try:
            result = self.execute_command('/system/resource/print')
            if result:
                resource = result[0]
                return {
                    'cpu_load': resource.get('cpu-load', '0'),
                    'free_memory': resource.get('free-memory', '0'),
                    'total_memory': resource.get('total-memory', '0'),
                    'free_hdd_space': resource.get('free-hdd-space', '0'),
                    'total_hdd_space': resource.get('total-hdd-space', '0'),
                    'uptime': resource.get('uptime', '0'),
                    'version': resource.get('version', 'غير معروف'),
                    'board_name': resource.get('board-name', 'غير معروف'),
                    'architecture': resource.get('architecture', 'غير معروف')
                }
            return {}
        except Exception as e:
            logger.error(f"خطأ في الحصول على موارد النظام: {e}")
            return {}

    # ==================== وظائف Hotspot ====================

    def get_hotspot_users(self) -> List[Dict]:
        """الحصول على قائمة مستخدمي Hotspot"""
        try:
            users = self.execute_command('/ip/hotspot/user/print')
            return [
                {
                    'id': user.get('.id', ''),
                    'name': user.get('name', 'غير معروف'),
                    'password': user.get('password', ''),
                    'profile': user.get('profile', 'default'),
                    'server': user.get('server', 'all'),
                    'address': user.get('address', ''),
                    'mac_address': user.get('mac-address', ''),
                    'comment': user.get('comment', ''),
                    'disabled': user.get('disabled', 'false') == 'true',
                    'limit_uptime': user.get('limit-uptime', ''),
                    'limit_bytes_in': user.get('limit-bytes-in', ''),
                    'limit_bytes_out': user.get('limit-bytes-out', '')
                }
                for user in users
            ]
        except Exception as e:
            logger.error(f"خطأ في الحصول على مستخدمي Hotspot: {e}")
            return []

    def create_hotspot_user(self, username: str, password: str, profile: str = 'default',
                           server: str = 'all', address: str = '', mac_address: str = '',
                           comment: str = '', limit_uptime: str = '',
                           limit_bytes_in: str = '', limit_bytes_out: str = '') -> bool:
        """إنشاء مستخدم Hotspot جديد"""
        try:
            params = {
                'name': username,
                'password': password,
                'profile': profile,
                'server': server
            }

            if address:
                params['address'] = address
            if mac_address:
                params['mac-address'] = mac_address
            if comment:
                params['comment'] = comment
            if limit_uptime:
                params['limit-uptime'] = limit_uptime
            if limit_bytes_in:
                params['limit-bytes-in'] = limit_bytes_in
            if limit_bytes_out:
                params['limit-bytes-out'] = limit_bytes_out

            self.execute_command('/ip/hotspot/user/add', params)
            logger.info(f"تم إنشاء مستخدم Hotspot {username} بنجاح")
            return True

        except Exception as e:
            logger.error(f"خطأ في إنشاء مستخدم Hotspot {username}: {e}")
            return False

    def delete_hotspot_user(self, user_id: str) -> bool:
        """حذف مستخدم Hotspot"""
        try:
            self.execute_command('/ip/hotspot/user/remove', {'.id': user_id})
            logger.info(f"تم حذف مستخدم Hotspot {user_id} بنجاح")
            return True
        except Exception as e:
            logger.error(f"خطأ في حذف مستخدم Hotspot {user_id}: {e}")
            return False

    def update_hotspot_user_password(self, user_id: str, new_password: str) -> bool:
        """تحديث كلمة مرور مستخدم Hotspot"""
        try:
            self.execute_command('/ip/hotspot/user/set', {
                '.id': user_id,
                'password': new_password
            })
            logger.info(f"تم تحديث كلمة مرور مستخدم Hotspot {user_id}")
            return True
        except Exception as e:
            logger.error(f"خطأ في تحديث كلمة مرور مستخدم Hotspot {user_id}: {e}")
            return False

    def enable_hotspot_user(self, user_id: str) -> bool:
        """تفعيل مستخدم Hotspot"""
        try:
            self.execute_command('/ip/hotspot/user/enable', {'.id': user_id})
            logger.info(f"تم تفعيل مستخدم Hotspot {user_id}")
            return True
        except Exception as e:
            logger.error(f"خطأ في تفعيل مستخدم Hotspot {user_id}: {e}")
            return False

    def disable_hotspot_user(self, user_id: str) -> bool:
        """تعطيل مستخدم Hotspot"""
        try:
            self.execute_command('/ip/hotspot/user/disable', {'.id': user_id})
            logger.info(f"تم تعطيل مستخدم Hotspot {user_id}")
            return True
        except Exception as e:
            logger.error(f"خطأ في تعطيل مستخدم Hotspot {user_id}: {e}")
            return False

    def get_hotspot_profiles(self) -> List[Dict]:
        """الحصول على قائمة ملفات Hotspot الشخصية"""
        try:
            profiles = self.execute_command('/ip/hotspot/user/profile/print')
            return [
                {
                    'id': profile.get('.id', ''),
                    'name': profile.get('name', 'غير معروف'),
                    'session_timeout': profile.get('session-timeout', ''),
                    'idle_timeout': profile.get('idle-timeout', ''),
                    'keepalive_timeout': profile.get('keepalive-timeout', ''),
                    'status_autorefresh': profile.get('status-autorefresh', ''),
                    'shared_users': profile.get('shared-users', ''),
                    'rate_limit': profile.get('rate-limit', '')
                }
                for profile in profiles
            ]
        except Exception as e:
            logger.error(f"خطأ في الحصول على ملفات Hotspot: {e}")
            return []

    def get_hotspot_servers(self) -> List[Dict]:
        """الحصول على قائمة خوادم Hotspot"""
        try:
            servers = self.execute_command('/ip/hotspot/print')
            return [
                {
                    'id': server.get('.id', ''),
                    'name': server.get('name', 'غير معروف'),
                    'interface': server.get('interface', ''),
                    'address_pool': server.get('address-pool', ''),
                    'profile': server.get('profile', ''),
                    'disabled': server.get('disabled', 'false') == 'true'
                }
                for server in servers
            ]
        except Exception as e:
            logger.error(f"خطأ في الحصول على خوادم Hotspot: {e}")
            return []

    def create_bulk_hotspot_users(self, prefix: str = '', count: int = 10, password_length: int = 8,
                                 profile: str = 'default', server: str = 'all',
                                 name_type: str = 'prefix', custom_names: List[str] = None) -> List[Dict]:
        """إنشاء عدد كبير من مستخدمي Hotspot مع دعم الأسماء العربية"""
        import random
        import string

        created_users = []

        # تحديد الأسماء حسب النوع
        if name_type == 'custom' and custom_names:
            usernames = custom_names
            count = len(usernames)
        else:
            usernames = []
            for i in range(1, count + 1):
                username = f"{prefix}{i:03d}"  # مثل: hotspot001, محمد001
                usernames.append(username)

        for username in usernames:
            # توليد كلمة مرور عشوائية
            password = ''.join(random.choices(
                string.ascii_letters + string.digits,
                k=password_length
            ))

            if self.create_hotspot_user(username, password, profile, server):
                created_users.append({
                    'username': username,
                    'password': password,
                    'profile': profile,
                    'server': server,
                    'type': 'hotspot',
                    'status': 'تم الإنشاء'
                })
            else:
                created_users.append({
                    'username': username,
                    'password': password,
                    'profile': profile,
                    'server': server,
                    'type': 'hotspot',
                    'status': 'فشل'
                })

        return created_users

    # ==================== وظائف التحكم المتقدمة ====================

    def set_user_speed_limit(self, user_id: str, user_type: str, upload_speed: str = '',
                           download_speed: str = '') -> bool:
        """تحديد حد السرعة للمستخدم"""
        try:
            rate_limit = ''
            if upload_speed and download_speed:
                rate_limit = f"{upload_speed}/{download_speed}"
            elif download_speed:
                rate_limit = f"0/{download_speed}"
            elif upload_speed:
                rate_limit = f"{upload_speed}/0"

            if user_type == 'hotspot':
                # للـ Hotspot نحتاج تحديث الملف الشخصي أو المستخدم مباشرة
                self.execute_command('/ip/hotspot/user/set', {
                    '.id': user_id,
                    'rate-limit': rate_limit
                })
            else:  # PPP
                # للـ PPP نحتاج تحديث الملف الشخصي
                self.execute_command('/ppp/secret/set', {
                    '.id': user_id,
                    'rate-limit': rate_limit
                })

            logger.info(f"تم تحديث حد السرعة للمستخدم {user_id}: {rate_limit}")
            return True

        except Exception as e:
            logger.error(f"خطأ في تحديد حد السرعة للمستخدم {user_id}: {e}")
            return False

    def set_user_data_limit(self, user_id: str, user_type: str, data_limit_gb: float = 0) -> bool:
        """تحديد حد البيانات للمستخدم بالجيجابايت"""
        try:
            if data_limit_gb <= 0:
                return True  # لا حد للبيانات

            # تحويل الجيجابايت إلى بايت
            data_limit_bytes = int(data_limit_gb * 1024 * 1024 * 1024)

            if user_type == 'hotspot':
                self.execute_command('/ip/hotspot/user/set', {
                    '.id': user_id,
                    'limit-bytes-total': str(data_limit_bytes)
                })
            else:  # PPP
                # للـ PPP نستخدم الملف الشخصي أو نضع تعليق
                self.execute_command('/ppp/secret/set', {
                    '.id': user_id,
                    'comment': f'حد البيانات: {data_limit_gb}GB'
                })

            logger.info(f"تم تحديد حد البيانات للمستخدم {user_id}: {data_limit_gb}GB")
            return True

        except Exception as e:
            logger.error(f"خطأ في تحديد حد البيانات للمستخدم {user_id}: {e}")
            return False

    def get_user_detailed_info(self, user_id: str, user_type: str) -> Dict:
        """الحصول على معلومات مفصلة للمستخدم"""
        try:
            if user_type == 'hotspot':
                users = self.execute_command('/ip/hotspot/user/print', {'.id': user_id})
            else:  # PPP
                users = self.execute_command('/ppp/secret/print', {'.id': user_id})

            if users:
                user = users[0]
                return {
                    'id': user.get('.id', ''),
                    'name': user.get('name', ''),
                    'password': user.get('password', ''),
                    'profile': user.get('profile', ''),
                    'comment': user.get('comment', ''),
                    'disabled': user.get('disabled', 'false') == 'true',
                    'rate_limit': user.get('rate-limit', ''),
                    'data_limit': user.get('limit-bytes-total', '') if user_type == 'hotspot' else '',
                    'type': user_type
                }
            return {}

        except Exception as e:
            logger.error(f"خطأ في الحصول على معلومات المستخدم {user_id}: {e}")
            return {}

    def get_users_by_profile(self, profile_name: str, user_type: str = 'both') -> List[Dict]:
        """الحصول على المستخدمين حسب الملف الشخصي"""
        try:
            users = []

            if user_type in ['ppp', 'both']:
                ppp_users = self.execute_command('/ppp/secret/print', {'?profile': profile_name})
                for user in ppp_users:
                    users.append({
                        'id': user.get('.id', ''),
                        'name': user.get('name', ''),
                        'password': user.get('password', ''),
                        'profile': user.get('profile', ''),
                        'comment': user.get('comment', ''),
                        'disabled': user.get('disabled', 'false') == 'true',
                        'type': 'ppp'
                    })

            if user_type in ['hotspot', 'both']:
                hotspot_users = self.execute_command('/ip/hotspot/user/print', {'?profile': profile_name})
                for user in hotspot_users:
                    users.append({
                        'id': user.get('.id', ''),
                        'name': user.get('name', ''),
                        'password': user.get('password', ''),
                        'profile': user.get('profile', ''),
                        'comment': user.get('comment', ''),
                        'disabled': user.get('disabled', 'false') == 'true',
                        'type': 'hotspot'
                    })

            return users

        except Exception as e:
            logger.error(f"خطأ في الحصول على المستخدمين حسب الملف {profile_name}: {e}")
            return []

    def get_users_by_comment(self, comment_text: str, user_type: str = 'both') -> List[Dict]:
        """الحصول على المستخدمين حسب التعليق"""
        try:
            users = []

            if user_type in ['ppp', 'both']:
                ppp_users = self.get_ppp_users()
                for user in ppp_users:
                    if comment_text.lower() in user.get('comment', '').lower():
                        users.append(user)

            if user_type in ['hotspot', 'both']:
                hotspot_users = self.get_hotspot_users()
                for user in hotspot_users:
                    if comment_text.lower() in user.get('comment', '').lower():
                        users.append(user)

            return users

        except Exception as e:
            logger.error(f"خطأ في البحث بالتعليق {comment_text}: {e}")
            return []
    
    def __enter__(self):
        """دعم استخدام with statement"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """إغلاق الاتصال عند الخروج من with statement"""
        self.disconnect()

# مثال على الاستخدام
if __name__ == "__main__":
    # إعدادات الاتصال
    HOST = "89.189.68.60"
    PORT = 2080  # منفذ API (ليس منفذ Winbox)
    USERNAME = "admin"
    PASSWORD = "khalid"
    
    # استخدام الأداة
    with MikroTikManager(HOST, USERNAME, PASSWORD, PORT) as mt:
        print("=== معلومات النظام ===")
        system_info = mt.get_system_info()
        if system_info:
            print(f"اسم الجهاز: {system_info.get('board-name', 'غير معروف')}")
            print(f"إصدار RouterOS: {system_info.get('version', 'غير معروف')}")
            print(f"وقت التشغيل: {system_info.get('uptime', 'غير معروف')}")
        
        print("\n=== المستخدمون المتصلون ===")
        users = mt.get_active_users()
        if users:
            for user in users:
                print(f"- {user['name']} ({user['type']}) - {user['address']}")
        else:
            print("لا يوجد مستخدمون متصلون")
        
        print("\n=== الواجهات ===")
        interfaces = mt.get_interfaces()
        for iface in interfaces[:5]:  # أول 5 واجهات فقط
            status = "نشط" if iface['running'] else "متوقف"
            print(f"- {iface['name']} ({iface['type']}) - {status}")

    def delete_ppp_user(self, username: str) -> bool:
        """حذف مستخدم PPP"""
        try:
            if not self.connect():
                return False
            
            # البحث عن المستخدم
            ppp_secrets = self.api.path('ppp', 'secret')
            users = list(ppp_secrets.select('name').where('name', username))
            
            if not users:
                logger.warning(f"المستخدم {username} غير موجود")
                return False
            
            # حذف المستخدم
            user_id = users[0]['.id']
            ppp_secrets.remove(user_id)
            
            logger.info(f"تم حذف مستخدم PPP: {username}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في حذف مستخدم PPP {username}: {e}")
            return False
        finally:
            self.disconnect()

    def delete_hotspot_user(self, username: str) -> bool:
        """حذف مستخدم Hotspot"""
        try:
            if not self.connect():
                return False
            
            # البحث عن المستخدم
            hotspot_users = self.api.path('ip', 'hotspot', 'user')
            users = list(hotspot_users.select('name').where('name', username))
            
            if not users:
                logger.warning(f"المستخدم {username} غير موجود")
                return False
            
            # حذف المستخدم
            user_id = users[0]['.id']
            hotspot_users.remove(user_id)
            
            logger.info(f"تم حذف مستخدم Hotspot: {username}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في حذف مستخدم Hotspot {username}: {e}")
            return False
        finally:
            self.disconnect()

    def toggle_ppp_user(self, username: str, disabled: bool) -> bool:
        """تفعيل/تعطيل مستخدم PPP"""
        try:
            if not self.connect():
                return False
            
            # البحث عن المستخدم
            ppp_secrets = self.api.path('ppp', 'secret')
            users = list(ppp_secrets.select('.id', 'name').where('name', username))
            
            if not users:
                logger.warning(f"المستخدم {username} غير موجود")
                return False
            
            # تحديث حالة المستخدم
            user_id = users[0]['.id']
            ppp_secrets.update(**{
                '.id': user_id,
                'disabled': 'yes' if disabled else 'no'
            })
            
            status = 'معطل' if disabled else 'مفعل'
            logger.info(f"تم تغيير حالة مستخدم PPP {username} إلى {status}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تغيير حالة مستخدم PPP {username}: {e}")
            return False
        finally:
            self.disconnect()

    def toggle_hotspot_user(self, username: str, disabled: bool) -> bool:
        """تفعيل/تعطيل مستخدم Hotspot"""
        try:
            if not self.connect():
                return False
            
            # البحث عن المستخدم
            hotspot_users = self.api.path('ip', 'hotspot', 'user')
            users = list(hotspot_users.select('.id', 'name').where('name', username))
            
            if not users:
                logger.warning(f"المستخدم {username} غير موجود")
                return False
            
            # تحديث حالة المستخدم
            user_id = users[0]['.id']
            hotspot_users.update(**{
                '.id': user_id,
                'disabled': 'yes' if disabled else 'no'
            })
            
            status = 'معطل' if disabled else 'مفعل'
            logger.info(f"تم تغيير حالة مستخدم Hotspot {username} إلى {status}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تغيير حالة مستخدم Hotspot {username}: {e}")
            return False
        finally:
            self.disconnect()

    def renew_ppp_user(self, username: str) -> bool:
        """تجديد مستخدم PPP (إعادة تعيين حدود البيانات)"""
        try:
            if not self.connect():
                return False
            
            # إعادة تعيين إحصائيات المستخدم
            ppp_active = self.api.path('ppp', 'active')
            active_users = list(ppp_active.select('.id', 'name').where('name', username))
            
            if active_users:
                # قطع الاتصال لإعادة تعيين الإحصائيات
                user_id = active_users[0]['.id']
                ppp_active.remove(user_id)
            
            logger.info(f"تم تجديد مستخدم PPP: {username}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تجديد مستخدم PPP {username}: {e}")
            return False
        finally:
            self.disconnect()

    def renew_hotspot_user(self, username: str) -> bool:
        """تجديد مستخدم Hotspot (إعادة تعيين حدود البيانات)"""
        try:
            if not self.connect():
                return False
            
            # إعادة تعيين إحصائيات المستخدم
            hotspot_active = self.api.path('ip', 'hotspot', 'active')
            active_users = list(hotspot_active.select('.id', 'user').where('user', username))
            
            if active_users:
                # قطع الاتصال لإعادة تعيين الإحصائيات
                for user in active_users:
                    hotspot_active.remove(user['.id'])
            
            logger.info(f"تم تجديد مستخدم Hotspot: {username}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تجديد مستخدم Hotspot {username}: {e}")
            return False
        finally:
            self.disconnect()

    def reset_ppp_user(self, username: str) -> bool:
        """إعادة ضبط مستخدم PPP (إعادة تعيين كلمة المرور)"""
        try:
            if not self.connect():
                return False
            
            # إنشاء كلمة مرور جديدة
            import random
            import string
            new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            
            # البحث عن المستخدم وتحديث كلمة المرور
            ppp_secrets = self.api.path('ppp', 'secret')
            users = list(ppp_secrets.select('.id', 'name').where('name', username))
            
            if not users:
                logger.warning(f"المستخدم {username} غير موجود")
                return False
            
            user_id = users[0]['.id']
            ppp_secrets.update(**{
                '.id': user_id,
                'password': new_password
            })
            
            logger.info(f"تم إعادة ضبط مستخدم PPP {username} بكلمة مرور جديدة: {new_password}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في إعادة ضبط مستخدم PPP {username}: {e}")
            return False
        finally:
            self.disconnect()

    def reset_hotspot_user(self, username: str) -> bool:
        """إعادة ضبط مستخدم Hotspot (إعادة تعيين كلمة المرور)"""
        try:
            if not self.connect():
                return False
            
            # إنشاء كلمة مرور جديدة
            import random
            import string
            new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            
            # البحث عن المستخدم وتحديث كلمة المرور
            hotspot_users = self.api.path('ip', 'hotspot', 'user')
            users = list(hotspot_users.select('.id', 'name').where('name', username))
            
            if not users:
                logger.warning(f"المستخدم {username} غير موجود")
                return False
            
            user_id = users[0]['.id']
            hotspot_users.update(**{
                '.id': user_id,
                'password': new_password
            })
            
            logger.info(f"تم إعادة ضبط مستخدم Hotspot {username} بكلمة مرور جديدة: {new_password}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في إعادة ضبط مستخدم Hotspot {username}: {e}")
            return False
        finally:
            self.disconnect()

    def get_hotspot_users(self) -> List[Dict[str, Any]]:
        """الحصول على قائمة مستخدمي Hotspot"""
        try:
            if not self.connect():
                return []
            
            hotspot_users = self.api.path('ip', 'hotspot', 'user')
            users_data = list(hotspot_users.select(
                'name', 'password', 'profile', 'server', 'disabled', 'comment'
            ))
            
            users = []
            for user in users_data:
                users.append({
                    'name': user.get('name', ''),
                    'password': user.get('password', ''),
                    'profile': user.get('profile', ''),
                    'server': user.get('server', ''),
                    'disabled': user.get('disabled', 'false'),
                    'comment': user.get('comment', ''),
                    'type': 'hotspot'
                })
            
            logger.info(f"تم جلب {len(users)} مستخدم Hotspot")
            return users
            
        except Exception as e:
            logger.error(f"خطأ في جلب مستخدمي Hotspot: {e}")
            return []
        finally:
            self.disconnect()

