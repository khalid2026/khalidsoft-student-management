#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تطبيق ويب لإدارة MikroTik
مطور بواسطة Augment Agent
"""

import qrcode
from io import BytesIO
import base64
from PIL import Imagefrom flask import Flask, render_template, jsonify, request, flash, redirect, url_for
from mikrotik_manager import MikroTikManager
import os
from dotenv import load_dotenv
import logging

# تحميل متغيرات البيئة
load_dotenv()

# إعداد التطبيق
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# إعدادات MikroTik من متغيرات البيئة
MIKROTIK_CONFIG = {
    'host': os.getenv('MIKROTIK_HOST', '89.189.68.60'),
    'port': int(os.getenv('MIKROTIK_PORT', '2080')),  # API port, not Winbox port
    'username': os.getenv('MIKROTIK_USERNAME', 'admin'),
    'password': os.getenv('MIKROTIK_PASSWORD', 'khalid')
}

def get_mikrotik_connection():
    """إنشاء اتصال MikroTik"""
    return MikroTikManager(
        host=MIKROTIK_CONFIG['host'],
        username=MIKROTIK_CONFIG['username'],
        password=MIKROTIK_CONFIG['password'],
        port=MIKROTIK_CONFIG['port']
    )

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    return render_template('index.html')

@app.route('/api/system-info')
def api_system_info():
    """API للحصول على معلومات النظام"""
    try:
        with get_mikrotik_connection() as mt:
            system_info = mt.get_system_info()
            return jsonify({
                'success': True,
                'data': system_info
            })
    except Exception as e:
        logger.error(f"خطأ في الحصول على معلومات النظام: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/active-users')
def api_active_users():
    """API للحصول على المستخدمين المتصلين"""
    try:
        with get_mikrotik_connection() as mt:
            users = mt.get_active_users()
            return jsonify({
                'success': True,
                'data': users,
                'count': len(users)
            })
    except Exception as e:
        logger.error(f"خطأ في الحصول على المستخدمين: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/interfaces')
def api_interfaces():
    """API للحصول على الواجهات"""
    try:
        with get_mikrotik_connection() as mt:
            interfaces = mt.get_interfaces()
            return jsonify({
                'success': True,
                'data': interfaces
            })
    except Exception as e:
        logger.error(f"خطأ في الحصول على الواجهات: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ip-addresses')
def api_ip_addresses():
    """API للحصول على عناوين IP"""
    try:
        with get_mikrotik_connection() as mt:
            addresses = mt.get_ip_addresses()
            return jsonify({
                'success': True,
                'data': addresses
            })
    except Exception as e:
        logger.error(f"خطأ في الحصول على عناوين IP: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/disconnect-user', methods=['POST'])
def api_disconnect_user():
    """API لقطع اتصال مستخدم"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        user_type = data.get('user_type', 'ppp')

        if not user_id:
            return jsonify({
                'success': False,
                'error': 'معرف المستخدم مطلوب'
            }), 400

        with get_mikrotik_connection() as mt:
            success = mt.disconnect_user(user_id, user_type)

            if success:
                return jsonify({
                    'success': True,
                    'message': 'تم قطع اتصال المستخدم بنجاح'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'فشل في قطع اتصال المستخدم'
                }), 500

    except Exception as e:
        logger.error(f"خطأ في قطع اتصال المستخدم: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ppp-secrets')
def api_ppp_secrets():
    """API للحصول على مستخدمي PPP"""
    try:
        with get_mikrotik_connection() as mt:
            secrets = mt.get_ppp_secrets()
            return jsonify({
                'success': True,
                'data': secrets
            })
    except Exception as e:
        logger.error(f"خطأ في الحصول على مستخدمي PPP: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/toggle-user', methods=['POST'])
def api_toggle_user():
    """API لتفعيل/تعطيل مستخدم"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        action = data.get('action')  # 'enable' or 'disable'

        if not user_id or not action:
            return jsonify({
                'success': False,
                'error': 'معرف المستخدم والإجراء مطلوبان'
            }), 400

        with get_mikrotik_connection() as mt:
            if action == 'enable':
                success = mt.enable_user(user_id)
                message = 'تم تفعيل المستخدم بنجاح'
            elif action == 'disable':
                success = mt.disable_user(user_id)
                message = 'تم تعطيل المستخدم بنجاح'
            else:
                return jsonify({
                    'success': False,
                    'error': 'إجراء غير صحيح'
                }), 400

            if success:
                return jsonify({
                    'success': True,
                    'message': message
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'فشل في تنفيذ الإجراء'
                }), 500

    except Exception as e:
        logger.error(f"خطأ في تفعيل/تعطيل المستخدم: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/user-traffic/<username>')
def api_user_traffic(username):
    """API للحصول على إحصائيات المستخدم"""
    try:
        with get_mikrotik_connection() as mt:
            traffic = mt.get_user_traffic(username)
            return jsonify({
                'success': True,
                'data': traffic
            })
    except Exception as e:
        logger.error(f"خطأ في الحصول على إحصائيات المستخدم: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/create-user', methods=['POST'])
def api_create_user():
    """API لإنشاء مستخدم جديد"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        profile = data.get('profile', 'default')
        local_address = data.get('local_address', '').strip()
        remote_address = data.get('remote_address', '').strip()
        service = data.get('service', 'any')

        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'اسم المستخدم وكلمة المرور مطلوبان'
            }), 400

        with get_mikrotik_connection() as mt:
            success = mt.create_ppp_user(
                username, password, profile,
                local_address, remote_address, service
            )

            if success:
                return jsonify({
                    'success': True,
                    'message': f'تم إنشاء المستخدم {username} بنجاح'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'فشل في إنشاء المستخدم'
                }), 500

    except Exception as e:
        logger.error(f"خطأ في إنشاء المستخدم: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/delete-user', methods=['POST'])
def api_delete_user():
    """API لحذف مستخدم"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({
                'success': False,
                'error': 'معرف المستخدم مطلوب'
            }), 400

        with get_mikrotik_connection() as mt:
            success = mt.delete_ppp_user(user_id)

            if success:
                return jsonify({
                    'success': True,
                    'message': 'تم حذف المستخدم بنجاح'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'فشل في حذف المستخدم'
                }), 500

    except Exception as e:
        logger.error(f"خطأ في حذف المستخدم: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/update-password', methods=['POST'])
def api_update_password():
    """API لتحديث كلمة مرور المستخدم"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        new_password = data.get('new_password', '').strip()

        if not user_id or not new_password:
            return jsonify({
                'success': False,
                'error': 'معرف المستخدم وكلمة المرور الجديدة مطلوبان'
            }), 400

        with get_mikrotik_connection() as mt:
            success = mt.update_user_password(user_id, new_password)

            if success:
                return jsonify({
                    'success': True,
                    'message': 'تم تحديث كلمة المرور بنجاح'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'فشل في تحديث كلمة المرور'
                }), 500

    except Exception as e:
        logger.error(f"خطأ في تحديث كلمة المرور: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ppp-profiles')
def api_ppp_profiles():
    """API للحصول على ملفات PPP الشخصية"""
    try:
        with get_mikrotik_connection() as mt:
            profiles = mt.get_ppp_profiles()
            return jsonify({
                'success': True,
                'data': profiles
            })
    except Exception as e:
        logger.error(f"خطأ في الحصول على ملفات PPP: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/create-bulk-users', methods=['POST'])
def api_create_bulk_users():
    """API لإنشاء مستخدمين بالجملة (PPP أو Hotspot) مع دعم الأسماء العربية"""
    try:
        data = request.get_json()
        prefix = data.get('prefix', 'user').strip()
        count = int(data.get('count', 10))
        password_length = int(data.get('password_length', 8))
        profile = data.get('profile', 'default')
        user_type = data.get('user_type', 'ppp')  # 'ppp' أو 'hotspot'
        server = data.get('server', 'all')  # للـ Hotspot فقط
        name_type = data.get('name_type', 'prefix')  # 'prefix', 'arabic', 'custom'
        custom_names = data.get('custom_names', [])  # للأسماء المخصصة

        # التحقق من الحد الأقصى
        if name_type == 'custom':
            count = len(custom_names)

        if count > 1000:  # حد أقصى للأمان
            return jsonify({
                'success': False,
                'error': 'العدد الأقصى المسموح هو 1000 مستخدم'
            }), 400

        with get_mikrotik_connection() as mt:
            if user_type == 'hotspot':
                created_users = mt.create_bulk_hotspot_users(
                    prefix, count, password_length, profile, server, name_type, custom_names
                )
            else:  # PPP
                created_users = mt.create_bulk_users(
                    prefix, count, password_length, profile, name_type, custom_names
                )

            success_count = len([u for u in created_users if u['status'] == 'تم الإنشاء'])

            return jsonify({
                'success': True,
                'message': f'تم إنشاء {success_count} من أصل {count} مستخدم {user_type.upper()}',
                'data': created_users,
                'summary': {
                    'total': count,
                    'success': success_count,
                    'failed': count - success_count,
                    'type': user_type,
                    'name_type': name_type
                }
            })

    except Exception as e:
        logger.error(f"خطأ في إنشاء المستخدمين بالجملة: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/system-resources')
def api_system_resources():
    """API للحصول على موارد النظام المفصلة"""
    try:
        with get_mikrotik_connection() as mt:
            resources = mt.get_system_resources()
            return jsonify({
                'success': True,
                'data': resources
            })
    except Exception as e:
        logger.error(f"خطأ في الحصول على موارد النظام: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== APIs لـ Hotspot ====================

@app.route('/api/hotspot-users')
def api_hotspot_users():
    """API للحصول على مستخدمي Hotspot"""
    try:
        with get_mikrotik_connection() as mt:
            users = mt.get_hotspot_users()
            return jsonify({
                'success': True,
                'data': users
            })
    except Exception as e:
        logger.error(f"خطأ في الحصول على مستخدمي Hotspot: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/create-hotspot-user', methods=['POST'])
def api_create_hotspot_user():
    """API لإنشاء مستخدم Hotspot جديد"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        profile = data.get('profile', 'default')
        server = data.get('server', 'all')
        address = data.get('address', '').strip()
        mac_address = data.get('mac_address', '').strip()
        comment = data.get('comment', '').strip()
        limit_uptime = data.get('limit_uptime', '').strip()
        limit_bytes_in = data.get('limit_bytes_in', '').strip()
        limit_bytes_out = data.get('limit_bytes_out', '').strip()

        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'اسم المستخدم وكلمة المرور مطلوبان'
            }), 400

        with get_mikrotik_connection() as mt:
            success = mt.create_hotspot_user(
                username, password, profile, server, address,
                mac_address, comment, limit_uptime, limit_bytes_in, limit_bytes_out
            )

            if success:
                return jsonify({
                    'success': True,
                    'message': f'تم إنشاء مستخدم Hotspot {username} بنجاح'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'فشل في إنشاء مستخدم Hotspot'
                }), 500

    except Exception as e:
        logger.error(f"خطأ في إنشاء مستخدم Hotspot: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/delete-hotspot-user', methods=['POST'])
def api_delete_hotspot_user():
    """API لحذف مستخدم Hotspot"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({
                'success': False,
                'error': 'معرف المستخدم مطلوب'
            }), 400

        with get_mikrotik_connection() as mt:
            success = mt.delete_hotspot_user(user_id)

            if success:
                return jsonify({
                    'success': True,
                    'message': 'تم حذف مستخدم Hotspot بنجاح'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'فشل في حذف مستخدم Hotspot'
                }), 500

    except Exception as e:
        logger.error(f"خطأ في حذف مستخدم Hotspot: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/update-hotspot-password', methods=['POST'])
def api_update_hotspot_password():
    """API لتحديث كلمة مرور مستخدم Hotspot"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        new_password = data.get('new_password', '').strip()

        if not user_id or not new_password:
            return jsonify({
                'success': False,
                'error': 'معرف المستخدم وكلمة المرور الجديدة مطلوبان'
            }), 400

        with get_mikrotik_connection() as mt:
            success = mt.update_hotspot_user_password(user_id, new_password)

            if success:
                return jsonify({
                    'success': True,
                    'message': 'تم تحديث كلمة مرور Hotspot بنجاح'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'فشل في تحديث كلمة مرور Hotspot'
                }), 500

    except Exception as e:
        logger.error(f"خطأ في تحديث كلمة مرور Hotspot: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/toggle-hotspot-user', methods=['POST'])
def api_toggle_hotspot_user():
    """API لتفعيل/تعطيل مستخدم Hotspot"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        action = data.get('action')  # 'enable' or 'disable'

        if not user_id or not action:
            return jsonify({
                'success': False,
                'error': 'معرف المستخدم والإجراء مطلوبان'
            }), 400

        with get_mikrotik_connection() as mt:
            if action == 'enable':
                success = mt.enable_hotspot_user(user_id)
                message = 'تم تفعيل مستخدم Hotspot بنجاح'
            elif action == 'disable':
                success = mt.disable_hotspot_user(user_id)
                message = 'تم تعطيل مستخدم Hotspot بنجاح'
            else:
                return jsonify({
                    'success': False,
                    'error': 'إجراء غير صحيح'
                }), 400

            if success:
                return jsonify({
                    'success': True,
                    'message': message
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'فشل في تنفيذ الإجراء'
                }), 500

    except Exception as e:
        logger.error(f"خطأ في تفعيل/تعطيل مستخدم Hotspot: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/hotspot-profiles')
def api_hotspot_profiles():
    """API للحصول على ملفات Hotspot الشخصية"""
    try:
        with get_mikrotik_connection() as mt:
            profiles = mt.get_hotspot_profiles()
            return jsonify({
                'success': True,
                'data': profiles
            })
    except Exception as e:
        logger.error(f"خطأ في الحصول على ملفات Hotspot: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/hotspot-servers')
def api_hotspot_servers():
    """API للحصول على خوادم Hotspot"""
    try:
        with get_mikrotik_connection() as mt:
            servers = mt.get_hotspot_servers()
            return jsonify({
                'success': True,
                'data': servers
            })
    except Exception as e:
        logger.error(f"خطأ في الحصول على خوادم Hotspot: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== APIs للصلاحيات المتقدمة ====================

@app.route('/api/set-user-speed', methods=['POST'])
def api_set_user_speed():
    """API لتحديد حد السرعة للمستخدم"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        user_type = data.get('user_type', 'ppp')
        upload_speed = data.get('upload_speed', '').strip()
        download_speed = data.get('download_speed', '').strip()

        if not user_id:
            return jsonify({
                'success': False,
                'error': 'معرف المستخدم مطلوب'
            }), 400

        with get_mikrotik_connection() as mt:
            success = mt.set_user_speed_limit(user_id, user_type, upload_speed, download_speed)

            if success:
                return jsonify({
                    'success': True,
                    'message': 'تم تحديث حد السرعة بنجاح'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'فشل في تحديث حد السرعة'
                }), 500

    except Exception as e:
        logger.error(f"خطأ في تحديد حد السرعة: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/set-user-data-limit', methods=['POST'])
def api_set_user_data_limit():
    """API لتحديد حد البيانات للمستخدم"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        user_type = data.get('user_type', 'ppp')
        data_limit_gb = float(data.get('data_limit_gb', 0))

        if not user_id:
            return jsonify({
                'success': False,
                'error': 'معرف المستخدم مطلوب'
            }), 400

        with get_mikrotik_connection() as mt:
            success = mt.set_user_data_limit(user_id, user_type, data_limit_gb)

            if success:
                return jsonify({
                    'success': True,
                    'message': f'تم تحديد حد البيانات إلى {data_limit_gb}GB'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'فشل في تحديد حد البيانات'
                }), 500

    except Exception as e:
        logger.error(f"خطأ في تحديد حد البيانات: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/user-detailed-info/<user_id>/<user_type>')
def api_user_detailed_info(user_id, user_type):
    """API للحصول على معلومات مفصلة للمستخدم"""
    try:
        with get_mikrotik_connection() as mt:
            user_info = mt.get_user_detailed_info(user_id, user_type)
            return jsonify({
                'success': True,
                'data': user_info
            })
    except Exception as e:
        logger.error(f"خطأ في الحصول على معلومات المستخدم: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/users-by-profile/<profile_name>')
@app.route('/api/users-by-profile/<profile_name>/<user_type>')
def api_users_by_profile(profile_name, user_type='both'):
    """API للحصول على المستخدمين حسب الملف الشخصي"""
    try:
        with get_mikrotik_connection() as mt:
            users = mt.get_users_by_profile(profile_name, user_type)
            return jsonify({
                'success': True,
                'data': users,
                'count': len(users)
            })
    except Exception as e:
        logger.error(f"خطأ في الحصول على المستخدمين حسب الملف: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/users-by-comment', methods=['POST'])
def api_users_by_comment():
    """API للحصول على المستخدمين حسب التعليق"""
    try:
        data = request.get_json()
        comment_text = data.get('comment', '').strip()
        user_type = data.get('user_type', 'both')

        if not comment_text:
            return jsonify({
                'success': False,
                'error': 'نص التعليق مطلوب'
            }), 400

        with get_mikrotik_connection() as mt:
            users = mt.get_users_by_comment(comment_text, user_type)
            return jsonify({
                'success': True,
                'data': users,
                'count': len(users)
            })
    except Exception as e:
        logger.error(f"خطأ في البحث بالتعليق: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/users')
def users_page():
    """صفحة المستخدمين"""
    return render_template('users.html')

@app.route('/users-management')
def users_management_page():
    """صفحة إدارة المستخدمين المتقدمة"""
    return render_template('users_management.html')

@app.route('/admin-panel')
def admin_panel():
    """لوحة الإدارة المتقدمة - خالد سوفت"""
    return render_template('admin_panel.html')

@app.route('/bulk-users')
def bulk_users_page():
    """صفحة إنشاء المستخدمين بالجملة"""
    return render_template('bulk_users.html')

@app.route('/reports')
def reports_page():
    """صفحة التقارير والإحصائيات"""
    return render_template('reports.html')

@app.route('/user-permissions')
def user_permissions_page():
    """صفحة إدارة صلاحيات المستخدمين"""
    return render_template('user_permissions.html')

@app.route('/network')
def network_page():
    """صفحة الشبكة"""
    return render_template('network.html')

@app.route('/settings')
def settings_page():
    """صفحة الإعدادات"""
    return render_template('settings.html', config=MIKROTIK_CONFIG)

@app.route('/test-connection')
def test_connection():
    """اختبار الاتصال"""
    try:
        mt = get_mikrotik_connection()
        if mt.connect():
            mt.disconnect()
            flash('تم الاتصال بنجاح! ✅', 'success')
        else:
            flash('فشل في الاتصال ❌', 'error')
    except Exception as e:
        flash(f'خطأ في الاتصال: {str(e)}', 'error')

    return redirect(url_for('settings_page'))

@app.route('/update-settings', methods=['POST'])
def update_settings():
    """تحديث إعدادات الاتصال"""
    try:
        # الحصول على البيانات من النموذج
        new_host = request.form.get('host', '').strip()
        new_port = request.form.get('port', '').strip()
        new_username = request.form.get('username', '').strip()
        new_password = request.form.get('password', '').strip()

        # التحقق من صحة البيانات
        if not new_host:
            flash('عنوان IP مطلوب ❌', 'error')
            return redirect(url_for('settings_page'))

        if not new_port or not new_port.isdigit():
            flash('المنفذ يجب أن يكون رقم صحيح ❌', 'error')
            return redirect(url_for('settings_page'))

        if not new_username:
            flash('اسم المستخدم مطلوب ❌', 'error')
            return redirect(url_for('settings_page'))

        if not new_password:
            flash('كلمة المرور مطلوبة ❌', 'error')
            return redirect(url_for('settings_page'))

        # تحديث الإعدادات في الذاكرة
        MIKROTIK_CONFIG['host'] = new_host
        MIKROTIK_CONFIG['port'] = int(new_port)
        MIKROTIK_CONFIG['username'] = new_username
        MIKROTIK_CONFIG['password'] = new_password

        # كتابة الإعدادات الجديدة في ملف .env
        env_content = f"""# إعدادات الاتصال بـ MikroTik
MIKROTIK_HOST={new_host}
MIKROTIK_PORT={new_port}
MIKROTIK_USERNAME={new_username}
MIKROTIK_PASSWORD={new_password}

# إعدادات التطبيق
FLASK_DEBUG=True
FLASK_PORT=8080
SECRET_KEY=your-secret-key-here-change-this"""

        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)

        flash('تم تحديث الإعدادات بنجاح! ✅', 'success')

        # اختبار الاتصال بالإعدادات الجديدة
        try:
            mt = get_mikrotik_connection()
            if mt.connect():
                mt.disconnect()
                flash('تم اختبار الاتصال بنجاح! 🎉', 'success')
            else:
                flash('تم حفظ الإعدادات لكن فشل اختبار الاتصال ⚠️', 'warning')
        except Exception as e:
            flash(f'تم حفظ الإعدادات لكن خطأ في اختبار الاتصال: {str(e)}', 'warning')

    except Exception as e:
        flash(f'خطأ في تحديث الإعدادات: {str(e)}', 'error')

    return redirect(url_for('settings_page'))

@app.errorhandler(404)
def not_found(error):
    """صفحة الخطأ 404"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """صفحة الخطأ 500"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    # إنشاء مجلد القوالب إذا لم يكن موجوداً
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # تشغيل التطبيق
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    port = int(os.getenv('FLASK_PORT', '5002'))
    
    print("🚀 تطبيق إدارة MikroTik")
    print(f"📡 الخادم: {MIKROTIK_CONFIG['host']}:{MIKROTIK_CONFIG['port']}")
    print(f"🌐 الواجهة: http://localhost:{port}")
    print("=" * 50)
    
    app.run(debug=debug_mode, port=port, host='0.0.0.0')

# وظائف QR Code والعملات المتنوعة
def generate_qr_code(data):
    """إنشاء QR code وإرجاعه كـ base64"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_base64}"

# العملات المدعومة
SUPPORTED_CURRENCIES = {
    'SAR': {'name': 'ريال سعودي', 'symbol': 'ر.س', 'code': 'SAR'},
    'MYR': {'name': 'رنجت ماليزي', 'symbol': 'RM', 'code': 'MYR'},
    'USD': {'name': 'دولار أمريكي', 'symbol': '$', 'code': 'USD'},
    'EUR': {'name': 'يورو', 'symbol': '€', 'code': 'EUR'},
    'AED': {'name': 'درهم إماراتي', 'symbol': 'د.إ', 'code': 'AED'},
    'KWD': {'name': 'دينار كويتي', 'symbol': 'د.ك', 'code': 'KWD'},
    'QAR': {'name': 'ريال قطري', 'symbol': 'ر.ق', 'code': 'QAR'},
    'BHD': {'name': 'دينار بحريني', 'symbol': 'د.ب', 'code': 'BHD'},
    'OMR': {'name': 'ريال عماني', 'symbol': 'ر.ع', 'code': 'OMR'},
    'JOD': {'name': 'دينار أردني', 'symbol': 'د.أ', 'code': 'JOD'},
    'EGP': {'name': 'جنيه مصري', 'symbol': 'ج.م', 'code': 'EGP'},
    'TRY': {'name': 'ليرة تركية', 'symbol': '₺', 'code': 'TRY'},
    'GBP': {'name': 'جنيه إسترليني', 'symbol': '£', 'code': 'GBP'},
    'JPY': {'name': 'ين ياباني', 'symbol': '¥', 'code': 'JPY'},
    'CNY': {'name': 'يوان صيني', 'symbol': '¥', 'code': 'CNY'},
    'INR': {'name': 'روبية هندية', 'symbol': '₹', 'code': 'INR'},
    'PKR': {'name': 'روبية باكستانية', 'symbol': '₨', 'code': 'PKR'},
    'BDT': {'name': 'تاكا بنغلاديشية', 'symbol': '৳', 'code': 'BDT'},
    'LKR': {'name': 'روبية سريلانكية', 'symbol': '₨', 'code': 'LKR'},
    'IDR': {'name': 'روبية إندونيسية', 'symbol': 'Rp', 'code': 'IDR'},
    'THB': {'name': 'بات تايلاندي', 'symbol': '฿', 'code': 'THB'},
    'SGD': {'name': 'دولار سنغافوري', 'symbol': 'S$', 'code': 'SGD'},
    'PHP': {'name': 'بيزو فلبيني', 'symbol': '₱', 'code': 'PHP'},
    'VND': {'name': 'دونغ فيتنامي', 'symbol': '₫', 'code': 'VND'},
    'KRW': {'name': 'وون كوري', 'symbol': '₩', 'code': 'KRW'},
    'RUB': {'name': 'روبل روسي', 'symbol': '₽', 'code': 'RUB'},
    'BRL': {'name': 'ريال برازيلي', 'symbol': 'R$', 'code': 'BRL'},
    'CAD': {'name': 'دولار كندي', 'symbol': 'C$', 'code': 'CAD'},
    'AUD': {'name': 'دولار أسترالي', 'symbol': 'A$', 'code': 'AUD'},
    'NZD': {'name': 'دولار نيوزيلندي', 'symbol': 'NZ$', 'code': 'NZD'},
    'ZAR': {'name': 'راند جنوب أفريقي', 'symbol': 'R', 'code': 'ZAR'},
    'NGN': {'name': 'نايرا نيجيرية', 'symbol': '₦', 'code': 'NGN'},
    'GHS': {'name': 'سيدي غاني', 'symbol': '₵', 'code': 'GHS'},
    'KES': {'name': 'شلن كيني', 'symbol': 'KSh', 'code': 'KES'},
    'UGX': {'name': 'شلن أوغندي', 'symbol': 'USh', 'code': 'UGX'},
    'TZS': {'name': 'شلن تنزاني', 'symbol': 'TSh', 'code': 'TZS'},
    'ETB': {'name': 'بير إثيوبي', 'symbol': 'Br', 'code': 'ETB'},
    'MAD': {'name': 'درهم مغربي', 'symbol': 'د.م', 'code': 'MAD'},
    'TND': {'name': 'دينار تونسي', 'symbol': 'د.ت', 'code': 'TND'},
    'DZD': {'name': 'دينار جزائري', 'symbol': 'د.ج', 'code': 'DZD'},
    'LYD': {'name': 'دينار ليبي', 'symbol': 'د.ل', 'code': 'LYD'},
    'SDG': {'name': 'جنيه سوداني', 'symbol': 'ج.س', 'code': 'SDG'},
    'SYP': {'name': 'ليرة سورية', 'symbol': 'ل.س', 'code': 'SYP'},
    'LBP': {'name': 'ليرة لبنانية', 'symbol': 'ل.ل', 'code': 'LBP'},
    'IQD': {'name': 'دينار عراقي', 'symbol': 'د.ع', 'code': 'IQD'},
    'IRR': {'name': 'ريال إيراني', 'symbol': '﷼', 'code': 'IRR'},
    'AFN': {'name': 'أفغاني', 'symbol': '؋', 'code': 'AFN'},
    'UZS': {'name': 'سوم أوزبكي', 'symbol': 'лв', 'code': 'UZS'},
    'KZT': {'name': 'تنغي كازاخي', 'symbol': '₸', 'code': 'KZT'},
    'KGS': {'name': 'سوم قيرغيزي', 'symbol': 'лв', 'code': 'KGS'},
    'TJS': {'name': 'سوموني طاجيكي', 'symbol': 'SM', 'code': 'TJS'},
    'TMT': {'name': 'مانات تركماني', 'symbol': 'T', 'code': 'TMT'},
    'AZN': {'name': 'مانات أذربيجاني', 'symbol': '₼', 'code': 'AZN'},
    'GEL': {'name': 'لاري جورجي', 'symbol': '₾', 'code': 'GEL'},
    'AMD': {'name': 'درام أرميني', 'symbol': '֏', 'code': 'AMD'},
    'BYN': {'name': 'روبل بيلاروسي', 'symbol': 'Br', 'code': 'BYN'},
    'UAH': {'name': 'هريفنيا أوكرانية', 'symbol': '₴', 'code': 'UAH'},
    'MDL': {'name': 'ليو مولدوفي', 'symbol': 'L', 'code': 'MDL'},
    'RON': {'name': 'ليو روماني', 'symbol': 'lei', 'code': 'RON'},
    'BGN': {'name': 'ليف بلغاري', 'symbol': 'лв', 'code': 'BGN'},
    'HRK': {'name': 'كونا كرواتية', 'symbol': 'kn', 'code': 'HRK'},
    'RSD': {'name': 'دينار صربي', 'symbol': 'Дин', 'code': 'RSD'},
    'BAM': {'name': 'مارك بوسني', 'symbol': 'KM', 'code': 'BAM'},
    'MKD': {'name': 'دينار مقدوني', 'symbol': 'ден', 'code': 'MKD'},
    'ALL': {'name': 'ليك ألباني', 'symbol': 'L', 'code': 'ALL'},
    'EUR': {'name': 'يورو', 'symbol': '€', 'code': 'EUR'},
}

@app.route('/api/currencies')
def get_currencies():
    """الحصول على قائمة العملات المدعومة"""
    return jsonify(SUPPORTED_CURRENCIES)

@app.route('/api/generate-qr')
def generate_qr():
    """إنشاء QR code للمستخدم"""
    username = request.args.get('username', '')
    password = request.args.get('password', '')
    profile = request.args.get('profile', '')
    server = request.args.get('server', '')
    
    # إنشاء النص للـ QR code
    qr_data = f"Username: {username}\nPassword: {password}"
    if profile:
        qr_data += f"\nProfile: {profile}"
    if server:
        qr_data += f"\nServer: {server}"
    
    qr_image = generate_qr_code(qr_data)
    return jsonify({'qr_code': qr_image})

@app.route('/api/print-cards')
def print_cards():
    """طباعة كروت المستخدمين مع QR codes"""
    users_data = request.args.get('users', '[]')
    currency = request.args.get('currency', 'SAR')
    price = request.args.get('price', '0')
    
    try:
        users = json.loads(users_data)
    except:
        users = []
    
    currency_info = SUPPORTED_CURRENCIES.get(currency, SUPPORTED_CURRENCIES['SAR'])
    
    # إنشاء QR codes للمستخدمين
    for user in users:
        if user.get('status') == 'تم الإنشاء':
            qr_data = f"Username: {user['username']}\nPassword: {user['password']}"
            if user.get('profile'):
                qr_data += f"\nProfile: {user['profile']}"
            if user.get('server'):
                qr_data += f"\nServer: {user['server']}"
            
            user['qr_code'] = generate_qr_code(qr_data)
    
    return jsonify({
        'users': users,
        'currency': currency_info,
        'price': price
    })


# APIs إدارة المستخدمين المتقدمة
@app.route('/api/delete-ppp-user', methods=['POST'])
def delete_ppp_user():
    """حذف مستخدم PPP"""
    try:
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({'success': False, 'message': 'اسم المستخدم مطلوب'})
        
        mikrotik = MikroTikManager(**MIKROTIK_CONFIG)
        result = mikrotik.delete_ppp_user(username)
        
        if result:
            return jsonify({'success': True, 'message': 'تم حذف المستخدم بنجاح'})
        else:
            return jsonify({'success': False, 'message': 'فشل في حذف المستخدم'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/delete-hotspot-user', methods=['POST'])
def delete_hotspot_user():
    """حذف مستخدم Hotspot"""
    try:
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({'success': False, 'message': 'اسم المستخدم مطلوب'})
        
        mikrotik = MikroTikManager(**MIKROTIK_CONFIG)
        result = mikrotik.delete_hotspot_user(username)
        
        if result:
            return jsonify({'success': True, 'message': 'تم حذف المستخدم بنجاح'})
        else:
            return jsonify({'success': False, 'message': 'فشل في حذف المستخدم'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/toggle-ppp-user', methods=['POST'])
def toggle_ppp_user():
    """تفعيل/تعطيل مستخدم PPP"""
    try:
        data = request.get_json()
        username = data.get('username')
        disabled = data.get('disabled', False)
        
        if not username:
            return jsonify({'success': False, 'message': 'اسم المستخدم مطلوب'})
        
        mikrotik = MikroTikManager(**MIKROTIK_CONFIG)
        result = mikrotik.toggle_ppp_user(username, disabled)
        
        if result:
            status = 'تعطيل' if disabled else 'تفعيل'
            return jsonify({'success': True, 'message': f'تم {status} المستخدم بنجاح'})
        else:
            return jsonify({'success': False, 'message': 'فشل في تغيير حالة المستخدم'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/toggle-hotspot-user', methods=['POST'])
def toggle_hotspot_user():
    """تفعيل/تعطيل مستخدم Hotspot"""
    try:
        data = request.get_json()
        username = data.get('username')
        disabled = data.get('disabled', False)
        
        if not username:
            return jsonify({'success': False, 'message': 'اسم المستخدم مطلوب'})
        
        mikrotik = MikroTikManager(**MIKROTIK_CONFIG)
        result = mikrotik.toggle_hotspot_user(username, disabled)
        
        if result:
            status = 'تعطيل' if disabled else 'تفعيل'
            return jsonify({'success': True, 'message': f'تم {status} المستخدم بنجاح'})
        else:
            return jsonify({'success': False, 'message': 'فشل في تغيير حالة المستخدم'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/renew-ppp-user', methods=['POST'])
def renew_ppp_user():
    """تجديد مستخدم PPP"""
    try:
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({'success': False, 'message': 'اسم المستخدم مطلوب'})
        
        mikrotik = MikroTikManager(**MIKROTIK_CONFIG)
        result = mikrotik.renew_ppp_user(username)
        
        if result:
            return jsonify({'success': True, 'message': 'تم تجديد المستخدم بنجاح'})
        else:
            return jsonify({'success': False, 'message': 'فشل في تجديد المستخدم'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/renew-hotspot-user', methods=['POST'])
def renew_hotspot_user():
    """تجديد مستخدم Hotspot"""
    try:
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({'success': False, 'message': 'اسم المستخدم مطلوب'})
        
        mikrotik = MikroTikManager(**MIKROTIK_CONFIG)
        result = mikrotik.renew_hotspot_user(username)
        
        if result:
            return jsonify({'success': True, 'message': 'تم تجديد المستخدم بنجاح'})
        else:
            return jsonify({'success': False, 'message': 'فشل في تجديد المستخدم'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/reset-ppp-user', methods=['POST'])
def reset_ppp_user():
    """إعادة ضبط مستخدم PPP"""
    try:
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({'success': False, 'message': 'اسم المستخدم مطلوب'})
        
        mikrotik = MikroTikManager(**MIKROTIK_CONFIG)
        result = mikrotik.reset_ppp_user(username)
        
        if result:
            return jsonify({'success': True, 'message': 'تم إعادة ضبط المستخدم بنجاح'})
        else:
            return jsonify({'success': False, 'message': 'فشل في إعادة ضبط المستخدم'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/reset-hotspot-user', methods=['POST'])
def reset_hotspot_user():
    """إعادة ضبط مستخدم Hotspot"""
    try:
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({'success': False, 'message': 'اسم المستخدم مطلوب'})
        
        mikrotik = MikroTikManager(**MIKROTIK_CONFIG)
        result = mikrotik.reset_hotspot_user(username)
        
        if result:
            return jsonify({'success': True, 'message': 'تم إعادة ضبط المستخدم بنجاح'})
        else:
            return jsonify({'success': False, 'message': 'فشل في إعادة ضبط المستخدم'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/hotspot-users')
def get_hotspot_users():
    """الحصول على مستخدمي Hotspot"""
    try:
        mikrotik = MikroTikManager(**MIKROTIK_CONFIG)
        users = mikrotik.get_hotspot_users()
        
        return jsonify({
            'success': True,
            'users': users
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'users': []
        })

