import telebot
import sqlite3
import random
import threading
import time
from datetime import datetime, timedelta

# إعدادات البوت
BOT_TOKEN = "8486663804:AAHoibAKxDtV0D0GANf8t_wcnntn89IQqUw"
ADMIN_IDS = [7427477368, 8065853069]
COMMISSION_RATE = 4.27
BOT_VERSION = "v2.0"

bot = telebot.TeleBot(BOT_TOKEN)
db_lock = threading.Lock()

# قواعد البيانات
def DREON_init_db():
    with db_lock:
        conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                balance REAL DEFAULT 0.0,
                registration_date TEXT,
                total_auctions INTEGER DEFAULT 0,
                total_bids INTEGER DEFAULT 0,
                last_activity TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auctions (
                auction_id TEXT PRIMARY KEY,
                seller_id INTEGER,
                item_type TEXT,
                item_description TEXT,
                start_price REAL,
                current_price REAL,
                current_bidder INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                end_time TEXT,
                admin_approved BOOLEAN DEFAULT FALSE,
                sold_price REAL DEFAULT 0,
                buyer_id INTEGER,
                bid_count INTEGER DEFAULT 0,
                views_count INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bids (
                bid_id INTEGER PRIMARY KEY AUTOINCREMENT,
                auction_id TEXT,
                bidder_id INTEGER,
                bid_amount REAL,
                bid_time TEXT,
                is_winner BOOLEAN DEFAULT FALSE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id TEXT PRIMARY KEY,
                user_id INTEGER,
                amount REAL,
                type TEXT,
                description TEXT,
                date TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_favorites (
                user_id INTEGER,
                auction_id TEXT,
                added_date TEXT,
                PRIMARY KEY (user_id, auction_id)
            )
        ''')
        
        conn.commit()
        conn.close()

DREON_init_db()

# وظائف مساعدة
def DREON_generate_auction_id():
    return f"AU{random.randint(100000, 999999)}"

def DREON_generate_transaction_id():
    return f"TXN{random.randint(100000000, 999999999)}"

def DREON_get_user_balance(user_id):
    with db_lock:
        conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0.0

def DREON_update_user_balance(user_id, amount):
    with db_lock:
        conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO users (user_id, balance, registration_date, last_activity) VALUES (?, 0, ?, ?)', 
                       (user_id, datetime.now().isoformat(), datetime.now().isoformat()))
        cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', 
                       (amount, user_id))
        conn.commit()
        conn.close()

def DREON_add_transaction(user_id, amount, transaction_type, description):
    with db_lock:
        conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
        cursor = conn.cursor()
        transaction_id = DREON_generate_transaction_id()
        cursor.execute('''
            INSERT INTO transactions (transaction_id, user_id, amount, type, description, date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (transaction_id, user_id, amount, transaction_type, description, datetime.now().isoformat()))
        conn.commit()
        conn.close()

def DREON_register_user(user_id, username=None, first_name=None):
    with db_lock:
        conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name, balance, registration_date, total_auctions, total_bids, last_activity)
            VALUES (?, ?, ?, 0, ?, 0, 0, ?)
        ''', (user_id, username, first_name, datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        conn.close()

def DREON_update_user_activity(user_id):
    with db_lock:
        conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET last_activity = ? WHERE user_id = ?', 
                       (datetime.now().isoformat(), user_id))
        conn.commit()
        conn.close()

def DREON_get_auction_details(auction_id):
    with db_lock:
        conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM auctions WHERE auction_id = ?', (auction_id,))
        result = cursor.fetchone()
        conn.close()
        return result

def DREON_increment_auction_views(auction_id):
    with db_lock:
        conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('UPDATE auctions SET views_count = views_count + 1 WHERE auction_id = ?', (auction_id,))
        conn.commit()
        conn.close()

def DREON_get_bid_history(auction_id, limit=10):
    with db_lock:
        conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT bidder_id, bid_amount, bid_time 
            FROM bids 
            WHERE auction_id = ? 
            ORDER BY bid_amount DESC
            LIMIT ?
        ''', (auction_id, limit))
        result = cursor.fetchall()
        conn.close()
        return result

def DREON_get_bot_stats():
    with db_lock:
        conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM auctions WHERE status = "active"')
        active_auctions = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM auctions WHERE status = "sold"')
        sold_auctions = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM auctions WHERE admin_approved = FALSE')
        pending_auctions = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(balance) FROM users')
        total_balance = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COUNT(*) FROM bids')
        total_bids = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(views_count) FROM auctions')
        total_views = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_users': total_users,
            'active_auctions': active_auctions,
            'sold_auctions': sold_auctions,
            'pending_auctions': pending_auctions,
            'total_balance': total_balance,
            'total_bids': total_bids,
            'total_views': total_views
        }

def DREON_complete_auction_sale(auction_id):
    with db_lock:
        conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('SELECT seller_id, current_price, current_bidder FROM auctions WHERE auction_id = ?', (auction_id,))
        auction = cursor.fetchone()
        
        if auction and auction[2]:
            seller_id, sold_price, buyer_id = auction
            
            commission = (sold_price * COMMISSION_RATE) / 100
            seller_amount = sold_price - commission
            
            DREON_update_user_balance(seller_id, seller_amount)
            DREON_add_transaction(seller_id, seller_amount, "بيع", f"مبلغ بيع المزاد {auction_id}")
            
            cursor.execute('''
                UPDATE auctions 
                SET status = "sold", sold_price = ?, buyer_id = ?
                WHERE auction_id = ?
            ''', (sold_price, buyer_id, auction_id))
            
            cursor.execute('UPDATE bids SET is_winner = TRUE WHERE auction_id = ? AND bidder_id = ?', 
                          (auction_id, buyer_id))
            
            conn.commit()
            
            try:
                bot.send_message(seller_id, f"تم بيع مزادك رقم {auction_id} بنجاح! السعر النهائي: {sold_price:.2f} نقطة. المبلغ المستلم: {seller_amount:.2f} نقطة (بعد خصم العمولة {COMMISSION_RATE}%)")
            except:
                pass
            
            try:
                bot.send_message(buyer_id, f"مبروك! فزت بالمزاد رقم {auction_id} بسعر {sold_price:.2f} نقطة. المنتج: {DREON_get_auction_details(auction_id)[3]}")
            except:
                pass
        else:
            cursor.execute('DELETE FROM auctions WHERE auction_id = ?', (auction_id,))
            conn.commit()
        
        conn.close()

def DREON_get_active_auctions_count():
    with db_lock:
        conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM auctions WHERE status = "active" AND admin_approved = TRUE')
        result = cursor.fetchone()[0]
        conn.close()
        return result

def DREON_get_user_active_bids(user_id):
    with db_lock:
        conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT a.auction_id, a.item_type, a.current_price, a.end_time
            FROM auctions a
            JOIN bids b ON a.auction_id = b.auction_id
            WHERE b.bidder_id = ? AND a.status = 'active'
        ''', (user_id,))
        result = cursor.fetchall()
        conn.close()
        return result

def DREON_add_to_favorites(user_id, auction_id):
    with db_lock:
        conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO user_favorites (user_id, auction_id, added_date)
                VALUES (?, ?, ?)
            ''', (user_id, auction_id, datetime.now().isoformat()))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()

def DREON_remove_from_favorites(user_id, auction_id):
    with db_lock:
        conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM user_favorites WHERE user_id = ? AND auction_id = ?', (user_id, auction_id))
        conn.commit()
        conn.close()

def DREON_get_user_favorites(user_id):
    with db_lock:
        conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.auction_id, a.item_type, a.current_price, a.end_time
            FROM auctions a
            JOIN user_favorites uf ON a.auction_id = uf.auction_id
            WHERE uf.user_id = ? AND a.status = 'active'
        ''', (user_id,))
        result = cursor.fetchall()
        conn.close()
        return result

def DREON_is_favorite(user_id, auction_id):
    with db_lock:
        conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM user_favorites WHERE user_id = ? AND auction_id = ?', (user_id, auction_id))
        result = cursor.fetchone()
        conn.close()
        return result is not None

# لوحات المفاتيح
def DREON_main_menu_inline(user_id):
    keyboard = telebot.types.InlineKeyboardMarkup()
    
    keyboard.row(
        telebot.types.InlineKeyboardButton("عرض المزادات", callback_data="active_auctions"),
        telebot.types.InlineKeyboardButton("إنشاء مزاد", callback_data="create_auction")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("رصيدي", callback_data="my_balance"),
        telebot.types.InlineKeyboardButton("مزاداتي", callback_data="my_auctions")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("مزايداتي", callback_data="my_active_bids"),
        telebot.types.InlineKeyboardButton("المفضلة", callback_data="my_favorites")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("إحصائيات", callback_data="user_stats"),
        telebot.types.InlineKeyboardButton("كيفية التواصل", callback_data="contact_info")
    )
    
    if user_id in ADMIN_IDS:
        keyboard.row(
            telebot.types.InlineKeyboardButton("لوحة الإدارة", callback_data="admin_panel")
        )
    
    keyboard.row(
        telebot.types.InlineKeyboardButton("تحديث", callback_data="main_menu")
    )
    
    return keyboard

def DREON_balance_menu_inline():
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        telebot.types.InlineKeyboardButton("شحن الرصيد", callback_data="charge_balance_user"),
        telebot.types.InlineKeyboardButton("خصم الرصيد", callback_data="deduct_balance_user")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("سجل المعاملات", callback_data="transaction_history"),
        telebot.types.InlineKeyboardButton("الرئيسية", callback_data="main_menu")
    )
    return keyboard

def DREON_contact_info_inline():
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        telebot.types.InlineKeyboardButton("تواصل مع المالك", url="https://t.me/example_owner")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("مجموعة الدعم", url="https://t.me/example_support_group"),
        telebot.types.InlineKeyboardButton("قناة البوت", url="https://t.me/example_bot_channel")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("الرئيسية", callback_data="main_menu")
    )
    return keyboard

def DREON_admin_panel_inline():
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        telebot.types.InlineKeyboardButton("المزادات المنتظرة", callback_data="pending_auctions"),
        telebot.types.InlineKeyboardButton("إحصائيات البوت", callback_data="bot_stats")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("شحن رصيد", callback_data="charge_balance"),
        telebot.types.InlineKeyboardButton("إدارة المستخدمين", callback_data="manage_users")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("المزادات المنتهية", callback_data="ended_auctions"),
        telebot.types.InlineKeyboardButton("إعلان عام", callback_data="broadcast")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("خصم رصيد", callback_data="deduct_balance"),
        telebot.types.InlineKeyboardButton("الرئيسية", callback_data="main_menu")
    )
    return keyboard

def DREON_auction_types_inline():
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        telebot.types.InlineKeyboardButton("معرفات سوشيال ميديا", callback_data="type_social_ids"),
        telebot.types.InlineKeyboardButton("حسابات سوشيال ميديا", callback_data="type_social_accounts")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("أرقام تليجرام", callback_data="type_telegram_numbers"),
        telebot.types.InlineKeyboardButton("أرقام واتساب", callback_data="type_whatsapp_numbers")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("قنوات تليجرام", callback_data="type_telegram_channels"),
        telebot.types.InlineKeyboardButton("مجموعات تليجرام", callback_data="type_telegram_groups")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("الرئيسية", callback_data="main_menu")
    )
    return keyboard

def DREON_auction_categories_inline():
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        telebot.types.InlineKeyboardButton("جميع المزادات", callback_data="category_all"),
        telebot.types.InlineKeyboardButton("معرفات سوشيال", callback_data="category_social_ids")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("حسابات سوشيال", callback_data="category_social_accounts"),
        telebot.types.InlineKeyboardButton("أرقام تليجرام", callback_data="category_telegram_numbers")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("أرقام واتساب", callback_data="category_whatsapp_numbers"),
        telebot.types.InlineKeyboardButton("قنوات تليجرام", callback_data="category_telegram_channels")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("مجموعات تليجرام", callback_data="category_telegram_groups")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("الرئيسية", callback_data="main_menu")
    )
    return keyboard

def DREON_auctions_list_inline(auctions, category="all", page=0, auctions_per_page=6):
    keyboard = telebot.types.InlineKeyboardMarkup()
    
    start_idx = page * auctions_per_page
    end_idx = start_idx + auctions_per_page
    page_auctions = auctions[start_idx:end_idx]
    
    for auction in page_auctions:
        auction_id, item_type, current_price, end_time, current_bidder, bid_count = auction
        end_time = datetime.fromisoformat(end_time)
        time_left = end_time - datetime.now()
        
        if time_left.total_seconds() > 0:
            short_type = item_type[:12] + "..." if len(item_type) > 12 else item_type
            button_text = f"{short_type} - {current_price:.0f}"
            keyboard.row(
                telebot.types.InlineKeyboardButton(button_text, callback_data=f"view_auction_{auction_id}")
            )
    
    navigation_buttons = []
    total_pages = max(1, (len(auctions) + auctions_per_page - 1) // auctions_per_page)
    
    if page > 0:
        navigation_buttons.append(telebot.types.InlineKeyboardButton("السابق", callback_data=f"page_{category}_{page-1}"))
    
    navigation_buttons.append(telebot.types.InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="current_page"))
    
    if page < total_pages - 1:
        navigation_buttons.append(telebot.types.InlineKeyboardButton("التالي", callback_data=f"page_{category}_{page+1}"))
    
    if navigation_buttons:
        keyboard.row(*navigation_buttons)
    
    keyboard.row(
        telebot.types.InlineKeyboardButton("تغيير التصنيف", callback_data="change_category"),
        telebot.types.InlineKeyboardButton("تحديث", callback_data=f"page_{category}_{page}")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("الرئيسية", callback_data="main_menu")
    )
    
    return keyboard

def DREON_auction_detail_inline(auction_id, user_id, show_refresh=True):
    keyboard = telebot.types.InlineKeyboardMarkup()
    
    auction = DREON_get_auction_details(auction_id)
    if not auction:
        return keyboard
    
    end_time = datetime.fromisoformat(auction[9])
    time_left = end_time - datetime.now()
    
    # التحقق من شروط إظهار زر المزايدة
    if (time_left.total_seconds() > 0 and 
        auction[7] == 'active' and 
        auction[10] and  # admin_approved
        auction[1] != user_id):  # ليس البائع
        keyboard.row(
            telebot.types.InlineKeyboardButton("مزايدة مخصصة", callback_data=f"bid_{auction_id}")
        )
    
    # زر المفضلة
    is_fav = DREON_is_favorite(user_id, auction_id)
    favorite_text = "إزالة من المفضلة" if is_fav else "إضافة للمفضلة"
    keyboard.row(
        telebot.types.InlineKeyboardButton(favorite_text, callback_data=f"favorite_{auction_id}"),
        telebot.types.InlineKeyboardButton("سجل المزايدات", callback_data=f"bid_history_{auction_id}")
    )
    
    control_buttons = []
    if show_refresh:
        control_buttons.append(telebot.types.InlineKeyboardButton("تحديث", callback_data=f"refresh_auction_{auction_id}"))
    
    control_buttons.append(telebot.types.InlineKeyboardButton("العودة للقائمة", callback_data="active_auctions"))
    
    if control_buttons:
        keyboard.row(*control_buttons)
    
    return keyboard

def DREON_bid_history_inline(auction_id):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        telebot.types.InlineKeyboardButton("العودة للمزاد", callback_data=f"view_auction_{auction_id}"),
        telebot.types.InlineKeyboardButton("الرئيسية", callback_data="main_menu")
    )
    return keyboard

def DREON_admin_auction_actions_inline(auction_id):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        telebot.types.InlineKeyboardButton("موافقة", callback_data=f"approve_{auction_id}"),
        telebot.types.InlineKeyboardButton("رفض", callback_data=f"reject_{auction_id}")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("عرض التفاصيل", callback_data=f"details_{auction_id}"),
        telebot.types.InlineKeyboardButton("سجل المزايدات", callback_data=f"bid_history_{auction_id}")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("العودة للقائمة", callback_data="pending_auctions")
    )
    return keyboard

def DREON_charge_balance_inline():
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        telebot.types.InlineKeyboardButton("شحن 100 نقطة", callback_data="charge_100"),
        telebot.types.InlineKeyboardButton("شحن 500 نقطة", callback_data="charge_500")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("شحن 1000 نقطة", callback_data="charge_1000"),
        telebot.types.InlineKeyboardButton("شحن 5000 نقطة", callback_data="charge_5000")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("إدخال مبلغ مخصص", callback_data="charge_custom")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("العودة للوحة", callback_data="admin_panel")
    )
    return keyboard

def DREON_deduct_balance_inline():
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        telebot.types.InlineKeyboardButton("خصم 100 نقطة", callback_data="deduct_100"),
        telebot.types.InlineKeyboardButton("خصم 500 نقطة", callback_data="deduct_500")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("خصم 1000 نقطة", callback_data="deduct_1000"),
        telebot.types.InlineKeyboardButton("خصم 5000 نقطة", callback_data="deduct_5000")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("إدخال مبلغ مخصص", callback_data="deduct_custom")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("العودة للوحة", callback_data="admin_panel")
    )
    return keyboard

def DREON_ended_auctions_inline(auction_id):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        telebot.types.InlineKeyboardButton("إكمال البيع", callback_data=f"complete_sale_{auction_id}"),
        telebot.types.InlineKeyboardButton("عرض التفاصيل", callback_data=f"details_{auction_id}")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("العودة للقائمة", callback_data="ended_auctions")
    )
    return keyboard

def DREON_favorites_inline():
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        telebot.types.InlineKeyboardButton("تحديث", callback_data="my_favorites"),
        telebot.types.InlineKeyboardButton("الرئيسية", callback_data="main_menu")
    )
    return keyboard

# معالجة الرسائل والأوامر
@bot.message_handler(commands=['start'])
def start_message(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        
        DREON_register_user(user_id, username, first_name)
        DREON_update_user_activity(user_id)
        
        active_count = DREON_get_active_auctions_count()
        user_balance = DREON_get_user_balance(user_id)
        
        welcome_text = f"""
مرحبا بك في DREON {BOT_VERSION}

نظام متكامل لبيع وشراء:
• معرفات وسائل التواصل الاجتماعي
• حسابات السوشيال ميديا  
• أرقام التليجرام والواتساب
• قنوات ومجموعات التليجرام

إحصائيات سريعة:
• المزادات النشطة: {active_count}
• رصيدك: {user_balance:.2f} نقطة

اختر الخيار المناسب من القائمة:
    """
        
        bot.send_message(message.chat.id, welcome_text, reply_markup=DREON_main_menu_inline(user_id))
    except Exception as e:
        print(f"خطأ في أمر start: {e}")
        bot.send_message(message.chat.id, "حدث خطأ أثناء بدء التشغيل. الرجاء المحاولة مرة أخرى.")

@bot.message_handler(commands=['stats'])
def stats_command(message):
    try:
        user_id = message.from_user.id
        DREON_update_user_activity(user_id)
        
        balance = DREON_get_user_balance(user_id)
        
        with db_lock:
            conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute('SELECT total_auctions, total_bids FROM users WHERE user_id = ?', (user_id,))
            user_stats = cursor.fetchone()
            
            cursor.execute('SELECT COUNT(*) FROM auctions WHERE seller_id = ? AND status = "active"', (user_id,))
            active_auctions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM auctions WHERE seller_id = ? AND status = "sold"', (user_id,))
            sold_auctions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM bids WHERE bidder_id = ?', (user_id,))
            total_bids = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM bids WHERE bidder_id = ? AND is_winner = TRUE', (user_id,))
            won_auctions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM user_favorites WHERE user_id = ?', (user_id,))
            total_favorites = cursor.fetchone()[0]
            
            conn.close()
        
        success_rate = ((won_auctions / total_bids) * 100) if total_bids > 0 else 0
        
        stats_text = f"""
إحصائياتك الشخصية - {BOT_VERSION}

المعلومات العامة:
• الرصيد الحالي: {balance:.2f} نقطة
• المزادات النشطة: {active_auctions}
• المزادات المباعة: {sold_auctions}

النشاط:
• إجمالي المزادات: {user_stats[0] if user_stats else 0}
• إجمالي المزايدات: {total_bids}
• المزادات المربوحة: {won_auctions}
• العناصر المفضلة: {total_favorites}

نسبة النجاح: {success_rate:.1f}%
        """
        
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton("رصيدي", callback_data="my_balance"),
            telebot.types.InlineKeyboardButton("مزاداتي", callback_data="my_auctions")
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton("مزايداتي", callback_data="my_active_bids"),
            telebot.types.InlineKeyboardButton("المفضلة", callback_data="my_favorites")
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton("الرئيسية", callback_data="main_menu")
        )
        
        bot.send_message(message.chat.id, stats_text, reply_markup=keyboard)
        
    except Exception as e:
        print(f"خطأ في أمر stats: {e}")
        bot.send_message(message.chat.id, "حدث خطأ في عرض الإحصائيات.")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    try:
        user_id = call.from_user.id
        DREON_update_user_activity(user_id)
        
        if call.data == "main_menu":
            DREON_show_main_menu(call)
        elif call.data == "active_auctions":
            DREON_show_auction_categories(call)
        elif call.data == "create_auction":
            DREON_create_auction_start(call)
        elif call.data == "my_balance":
            DREON_show_balance(call)
        elif call.data == "my_auctions":
            DREON_show_my_auctions(call)
        elif call.data == "my_active_bids":
            DREON_show_my_active_bids(call)
        elif call.data == "my_favorites":
            DREON_show_my_favorites(call)
        elif call.data == "user_stats":
            DREON_show_user_stats(call)
        elif call.data == "contact_info":
            DREON_show_contact_info(call)
        elif call.data == "charge_balance_user":
            DREON_show_charge_info(call)
        elif call.data == "deduct_balance_user":
            DREON_show_deduct_info(call)
        elif call.data == "transaction_history":
            DREON_show_transaction_history(call)
        elif call.data == "admin_panel":
            if user_id in ADMIN_IDS:
                DREON_show_admin_panel(call)
            else:
                bot.answer_callback_query(call.id, "غير مسموح لك بالوصول لهذه اللوحة")
        elif call.data == "pending_auctions":
            if user_id in ADMIN_IDS:
                DREON_show_pending_auctions(call)
            else:
                bot.answer_callback_query(call.id, "غير مسموح")
        elif call.data == "bot_stats":
            if user_id in ADMIN_IDS:
                DREON_show_bot_stats(call)
            else:
                bot.answer_callback_query(call.id, "غير مسموح")
        elif call.data == "charge_balance":
            if user_id in ADMIN_IDS:
                DREON_charge_balance_menu(call)
            else:
                bot.answer_callback_query(call.id, "غير مسموح")
        elif call.data == "deduct_balance":
            if user_id in ADMIN_IDS:
                DREON_deduct_balance_menu(call)
            else:
                bot.answer_callback_query(call.id, "غير مسموح")
        elif call.data == "manage_users":
            if user_id in ADMIN_IDS:
                DREON_manage_users(call)
            else:
                bot.answer_callback_query(call.id, "غير مسموح")
        elif call.data == "ended_auctions":
            if user_id in ADMIN_IDS:
                DREON_show_ended_auctions(call)
            else:
                bot.answer_callback_query(call.id, "غير مسموح")
        elif call.data == "broadcast":
            if user_id in ADMIN_IDS:
                DREON_start_broadcast(call)
            else:
                bot.answer_callback_query(call.id, "غير مسموح")
        elif call.data.startswith("category_"):
            DREON_show_auctions_by_category(call)
        elif call.data.startswith("page_"):
            DREON_handle_page_navigation(call)
        elif call.data == "change_category":
            DREON_show_auction_categories(call)
        elif call.data.startswith("view_auction_"):
            DREON_show_auction_detail(call)
        elif call.data.startswith("refresh_auction_"):
            DREON_handle_refresh_auction(call)
        elif call.data.startswith("bid_"):
            DREON_handle_bid_request(call)
        elif call.data.startswith("favorite_"):
            DREON_handle_favorite_toggle(call)
        elif call.data.startswith("type_"):
            DREON_handle_auction_type_selection(call)
        elif call.data.startswith("approve_"):
            if user_id in ADMIN_IDS:
                DREON_handle_auction_approval(call)
            else:
                bot.answer_callback_query(call.id, "غير مسموح")
        elif call.data.startswith("reject_"):
            if user_id in ADMIN_IDS:
                DREON_handle_auction_rejection(call)
            else:
                bot.answer_callback_query(call.id, "غير مسموح")
        elif call.data.startswith("bid_history_"):
            DREON_show_bid_history(call)
        elif call.data.startswith("details_"):
            DREON_show_auction_details(call)
        elif call.data.startswith("charge_"):
            if user_id in ADMIN_IDS:
                DREON_handle_charge_balance(call)
            else:
                bot.answer_callback_query(call.id, "غير مسموح")
        elif call.data.startswith("deduct_"):
            if user_id in ADMIN_IDS:
                DREON_handle_deduct_balance(call)
            else:
                bot.answer_callback_query(call.id, "غير مسموح")
        elif call.data.startswith("complete_sale_"):
            if user_id in ADMIN_IDS:
                DREON_handle_complete_sale(call)
            else:
                bot.answer_callback_query(call.id, "غير مسموح")
    
    except Exception as e:
        print(f"خطأ في معالجة الاستعلام: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ، الرجاء المحاولة مرة أخرى")

# دوال العرض والتنقل
def DREON_show_main_menu(call):
    try:
        user_id = call.from_user.id
        active_count = DREON_get_active_auctions_count()
        balance = DREON_get_user_balance(user_id)
        
        menu_text = f"""
القائمة الرئيسية - {BOT_VERSION}

لمحة سريعة:
• المزادات النشطة: {active_count}
• رصيدك: {balance:.2f} نقطة

اختر من الخيارات التالية:
    """
        
        bot.edit_message_text(
            menu_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=DREON_main_menu_inline(user_id)
        )
    except Exception as e:
        print(f"خطأ في show_main_menu: {e}")
        bot.send_message(call.message.chat.id, menu_text, reply_markup=DREON_main_menu_inline(user_id))

def DREON_show_contact_info(call):
    try:
        contact_text = f"""
معلومات التواصل - {BOT_VERSION}

للتواصل معنا يمكنك استخدام الروابط التالية:

• تواصل مباشر مع المالك للمساعدة الفورية
• مجموعة الدعم للمساعدة والمشورة
• قناة البوت لأخر التحديثات والإعلانات

اختر طريقة التواصل المناسبة:
    """
        
        bot.edit_message_text(
            contact_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=DREON_contact_info_inline()
        )
    except:
        bot.send_message(call.message.chat.id, contact_text, reply_markup=DREON_contact_info_inline())

def DREON_show_charge_info(call):
    try:
        user_id = call.from_user.id
        balance = DREON_get_user_balance(user_id)
        
        charge_text = f"""
شحن الرصيد

رصيدك الحالي: {balance:.2f} نقطة

لشحن الرصيد في حسابك، يرجى التواصل مع الإدارة عبر:
• مجموعة الدعم: @example_support_group
• المالك: @example_owner

سيقوم فريق الدعم بمساعدتك في عملية الشحن بسرعة وسهولة.
    """
        
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton("مجموعة الدعم", url="https://t.me/example_support_group"),
            telebot.types.InlineKeyboardButton("تواصل مع المالك", url="https://t.me/example_owner")
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton("العودة للرصيد", callback_data="my_balance"),
            telebot.types.InlineKeyboardButton("الرئيسية", callback_data="main_menu")
        )
        
        bot.edit_message_text(
            charge_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except:
        bot.send_message(call.message.chat.id, charge_text, reply_markup=keyboard)

def DREON_show_deduct_info(call):
    try:
        user_id = call.from_user.id
        balance = DREON_get_user_balance(user_id)
        
        deduct_text = f"""
خصم الرصيد

رصيدك الحالي: {balance:.2f} نقطة

لطلب خصم رصيد أو سحبه من حسابك، يرجى التواصل مع الإدارة عبر:
• مجموعة الدعم: @example_support_group
• المالك: @example_owner

ملاحظة: قد تطبق رسوم على عملية السحب حسب المبلغ.
    """
        
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton("مجموعة الدعم", url="https://t.me/example_support_group"),
            telebot.types.InlineKeyboardButton("تواصل مع المالك", url="https://t.me/example_owner")
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton("العودة للرصيد", callback_data="my_balance"),
            telebot.types.InlineKeyboardButton("الرئيسية", callback_data="main_menu")
        )
        
        bot.edit_message_text(
            deduct_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except:
        bot.send_message(call.message.chat.id, deduct_text, reply_markup=keyboard)

def DREON_show_transaction_history(call):
    try:
        user_id = call.from_user.id
        
        with db_lock:
            conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT type, amount, description, date 
                FROM transactions 
                WHERE user_id = ? 
                ORDER BY date DESC 
                LIMIT 10
            ''', (user_id,))
            transactions = cursor.fetchall()
            conn.close()
        
        if not transactions:
            history_text = "لا توجد معاملات سابقة"
        else:
            history_text = "سجل المعاملات الأخيرة:\n\n"
            for i, transaction in enumerate(transactions, 1):
                trans_type, amount, description, date = transaction
                trans_date = datetime.fromisoformat(date)
                date_str = trans_date.strftime('%Y-%m-%d %H:%M')
                
                sign = "+" if trans_type in ["شحن", "بيع", "استرجاع"] else "-"
                history_text += f"{i}. {description}: {sign}{amount:.2f} نقطة\n   {date_str}\n\n"
        
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton("العودة للرصيد", callback_data="my_balance"),
            telebot.types.InlineKeyboardButton("الرئيسية", callback_data="main_menu")
        )
        
        bot.edit_message_text(
            history_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except:
        bot.send_message(call.message.chat.id, history_text, reply_markup=keyboard)

def DREON_show_user_stats(call):
    try:
        user_id = call.from_user.id
        balance = DREON_get_user_balance(user_id)
        
        with db_lock:
            conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute('SELECT total_auctions, total_bids FROM users WHERE user_id = ?', (user_id,))
            user_stats = cursor.fetchone()
            
            cursor.execute('SELECT COUNT(*) FROM auctions WHERE seller_id = ? AND status = "active"', (user_id,))
            active_auctions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM auctions WHERE seller_id = ? AND status = "sold"', (user_id,))
            sold_auctions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM bids WHERE bidder_id = ?', (user_id,))
            total_bids = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM bids WHERE bidder_id = ? AND is_winner = TRUE', (user_id,))
            won_auctions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM user_favorites WHERE user_id = ?', (user_id,))
            total_favorites = cursor.fetchone()[0]
            
            conn.close()
        
        success_rate = ((won_auctions / total_bids) * 100) if total_bids > 0 else 0
        
        stats_text = f"""
إحصائياتك الشخصية - {BOT_VERSION}

المعلومات العامة:
• الرصيد الحالي: {balance:.2f} نقطة
• المزادات النشطة: {active_auctions}
• المزادات المباعة: {sold_auctions}

النشاط:
• إجمالي المزادات: {user_stats[0] if user_stats else 0}
• إجمالي المزايدات: {total_bids}
• المزادات المربوحة: {won_auctions}
• العناصر المفضلة: {total_favorites}

نسبة النجاح: {success_rate:.1f}%
    """
        
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton("رصيدي", callback_data="my_balance"),
            telebot.types.InlineKeyboardButton("مزاداتي", callback_data="my_auctions")
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton("مزايداتي", callback_data="my_active_bids"),
            telebot.types.InlineKeyboardButton("المفضلة", callback_data="my_favorites")
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton("الرئيسية", callback_data="main_menu")
        )
        
        bot.edit_message_text(
            stats_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"خطأ في show_user_stats: {e}")
        bot.send_message(call.message.chat.id, "حدث خطأ في عرض الإحصائيات.")

# نظام المزايدة
def DREON_handle_bid_request(call):
    try:
        auction_id = call.data.replace("bid_", "")
        user_id = call.from_user.id
        auction = DREON_get_auction_details(auction_id)
        
        if not auction:
            bot.answer_callback_query(call.id, "المزاد غير موجود")
            return
        
        if auction[7] != 'active' or not auction[10]:
            bot.answer_callback_query(call.id, "المزاد غير متاح للمزايدة")
            return
        
        if auction[1] == user_id:
            bot.answer_callback_query(call.id, "لا يمكنك المزايدة على مزادك الخاص")
            return
        
        end_time = datetime.fromisoformat(auction[9])
        if datetime.now() > end_time:
            bot.answer_callback_query(call.id, "انتهى وقت المزاد")
            return
        
        current_price = auction[5]
        min_bid = current_price * 1.05
        user_balance = DREON_get_user_balance(user_id)
        
        bid_info = f"""
المزايدة المخصصة

رقم المزاد: {auction_id}
النوع: {auction[2]}
السعر الحالي: {current_price:.2f} نقطة
الحد الأدنى: {min_bid:.2f} نقطة
رصيدك: {user_balance:.2f} نقطة

أدخل مبلغ المزايدة:
        """
        
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, bid_info)
        bot.register_next_step_handler(msg, DREON_process_bid_amount, auction_id, user_id, min_bid)
        
    except Exception as e:
        print(f"خطأ في طلب المزايدة: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ أثناء طلب المزايدة")

def DREON_process_bid_amount(message, auction_id, user_id, min_bid):
    try:
        bid_text = message.text.strip().replace(',', '').replace(' ', '')
        bid_amount = float(bid_text)
        bid_amount = round(bid_amount, 2)
        
        if bid_amount <= 0:
            bot.send_message(message.chat.id, "المبلغ يجب أن يكون أكبر من الصفر.")
            return
            
    except ValueError:
        bot.send_message(message.chat.id, "المبلغ غير صالح. الرجاء إدخال رقم صحيح أو عشري (مثال: 150.50)")
        return
    
    auction = DREON_get_auction_details(auction_id)
    
    if not auction:
        bot.send_message(message.chat.id, "المزاد غير موجود أو تم حذفه")
        return
    
    if auction[7] != 'active' or not auction[10]:
        bot.send_message(message.chat.id, "المزاد غير متاح للمزايدة حالياً")
        return
    
    if auction[1] == user_id:
        bot.send_message(message.chat.id, "لا يمكنك المزايدة على مزادك الخاص")
        return
    
    end_time = datetime.fromisoformat(auction[9])
    if datetime.now() > end_time:
        bot.send_message(message.chat.id, "انتهى وقت المزاد")
        return
    
    current_price = auction[5]
    actual_min_bid = current_price * 1.05

    if bid_amount < actual_min_bid:
        bot.send_message(message.chat.id, f"المبلغ أقل من الحد الأدنى للمزايدة\nالحد الأدنى المطلوب: {actual_min_bid:.2f} نقطة")
        return
    
    user_balance = DREON_get_user_balance(user_id)
    if user_balance < bid_amount:
        bot.send_message(message.chat.id, f"رصيدك غير كافي\nتحتاج: {bid_amount:.2f} نقطة\nرصيدك الحالي: {user_balance:.2f} نقطة")
        return
    
    with db_lock:
        conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
        cursor = conn.cursor()
        
        try:
            previous_bidder = auction[6]
            if previous_bidder and previous_bidder != user_id:
                previous_bid = auction[5]
                DREON_update_user_balance(previous_bidder, previous_bid)
                DREON_add_transaction(previous_bidder, previous_bid, "استرجاع", f"استرجاع مبلغ مزايدة - {auction_id}")
                
                try:
                    bot.send_message(previous_bidder, f"تم تجاوز مزايدتك في المزاد {auction_id}. تم استرجاع {previous_bid:.2f} نقطة لحسابك.")
                except:
                    pass
            
            DREON_update_user_balance(user_id, -bid_amount)
            DREON_add_transaction(user_id, -bid_amount, "مزايدة", f"مبلغ مزايدة - {auction_id}")
            
            cursor.execute('''
                UPDATE auctions 
                SET current_price = ?, current_bidder = ?, bid_count = bid_count + 1
                WHERE auction_id = ?
            ''', (bid_amount, user_id, auction_id))
            
            cursor.execute('''
                INSERT INTO bids (auction_id, bidder_id, bid_amount, bid_time)
                VALUES (?, ?, ?, ?)
            ''', (auction_id, user_id, bid_amount, datetime.now().isoformat()))
            
            cursor.execute('UPDATE users SET total_bids = total_bids + 1 WHERE user_id = ?', (user_id,))
            conn.commit()
            
            try:
                bot.send_message(auction[1], f"مزايدة جديدة على مزادك {auction_id}. المبلغ: {bid_amount:.2f} نقطة")
            except:
                pass
            
            success_msg = f"""
تمت المزايدة بنجاح!

رقم المزاد: {auction_id}
مبلغ المزايدة: {bid_amount:.2f} نقطة
أنت الآن المزايد الحالي

سيتم إشعارك إذا تم تجاوز مزايدتك
            """
            bot.send_message(message.chat.id, success_msg)
            
            DREON_update_auction_display(message.chat.id, auction_id, user_id)
            
        except Exception as e:
            conn.rollback()
            print(f"خطأ في تنفيذ المزايدة: {e}")
            bot.send_message(message.chat.id, "حدث خطأ أثناء تنفيذ المزايدة. الرجاء المحاولة مرة أخرى.")
        
        finally:
            conn.close()

def DREON_update_auction_display(chat_id, auction_id, user_id):
    auction = DREON_get_auction_details(auction_id)
    if not auction:
        return
    
    end_time = datetime.fromisoformat(auction[9])
    time_left = end_time - datetime.now()
    
    if time_left.total_seconds() <= 0:
        auction_text = f"""
المزاد منتهي

رقم المزاد: {auction_id}
النوع: {auction[2]}
الوصف: {auction[3]}
السعر النهائي: {auction[5]:.2f} نقطة
المزايد الفائز: {auction[6] if auction[6] else "لا يوجد"}
        """
    else:
        hours = int(time_left.total_seconds() // 3600)
        minutes = int((time_left.total_seconds() % 3600) // 60)
        
        current_bidder_text = "أنت" if auction[6] == user_id else f"المستخدم {auction[6]}" if auction[6] else "لا يوجد"
        
        auction_text = f"""
تفاصيل المزاد

رقم المزاد: {auction_id}
النوع: {auction[2]}
الوصف: {auction[3]}
السعر الحالي: {auction[5]:.2f} نقطة
المزايد الحالي: {current_bidder_text}
عدد المزايدات: {auction[13]}

معلومات الوقت:
• بدأ في: {datetime.fromisoformat(auction[8]).strftime('%Y-%m-%d %H:%M')}
• ينتهي في: {end_time.strftime('%Y-%m-%d %H:%M')}
• الوقت المتبقي: {hours} ساعة {minutes} دقيقة
        """
    
    try:
        bot.send_message(chat_id, auction_text, reply_markup=DREON_auction_detail_inline(auction_id, user_id))
    except Exception as e:
        print(f"خطأ في تحديث عرض المزاد: {e}")

# دوال إضافية للعرض
def DREON_show_auction_detail(call, show_refresh=True):
    try:
        auction_id = call.data.replace("view_auction_", "")
        user_id = call.from_user.id
        auction = DREON_get_auction_details(auction_id)
        
        if not auction:
            bot.answer_callback_query(call.id, "المزاد غير موجود")
            return
        
        DREON_increment_auction_views(auction_id)
        
        end_time = datetime.fromisoformat(auction[9])
        time_left = end_time - datetime.now()
        
        if time_left.total_seconds() <= 0:
            auction_text = f"""
تفاصيل المزاد

رقم المزاد: {auction_id}
النوع: {auction[2]}
الوصف: {auction[3]}
السعر النهائي: {auction[5]:.2f} نقطة
المزايد الفائز: {auction[6] if auction[6] else "لا يوجد"}
عدد المزايدات: {auction[13]}
عدد المشاهدات: {auction[14]}

انتهى وقت المزاد
            """
        else:
            hours = int(time_left.total_seconds() // 3600)
            minutes = int((time_left.total_seconds() % 3600) // 60)
            
            current_bidder_text = "أنت" if auction[6] == user_id else f"المستخدم {auction[6]}" if auction[6] else "لا يوجد"
            
            auction_text = f"""
تفاصيل المزاد

رقم المزاد: {auction_id}
النوع: {auction[2]}
الوصف: {auction[3]}
السعر الحالي: {auction[5]:.2f} نقطة
المزايد الحالي: {current_bidder_text}
عدد المزايدات: {auction[13]}
عدد المشاهدات: {auction[14]}

معلومات الوقت:
• بدأ في: {datetime.fromisoformat(auction[8]).strftime('%Y-%m-%d %H:%M')}
• ينتهي في: {end_time.strftime('%Y-%m-%d %H:%M')}
• الوقت المتبقي: {hours} ساعة {minutes} دقيقة
            """
        
        bot.edit_message_text(
            auction_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=DREON_auction_detail_inline(auction_id, user_id, show_refresh)
        )
        
    except Exception as e:
        print(f"خطأ في عرض تفاصيل المزاد: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في عرض التفاصيل")

def DREON_handle_refresh_auction(call):
    DREON_show_auction_detail(call)

def DREON_show_balance(call):
    try:
        user_id = call.from_user.id
        balance = DREON_get_user_balance(user_id)
        
        with db_lock:
            conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM auctions WHERE seller_id = ?', (user_id,))
            total_auctions = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM bids WHERE bidder_id = ?', (user_id,))
            total_bids = cursor.fetchone()[0]
            conn.close()
        
        balance_text = f"""
رصيدك الحالي

المعلومات الشخصية:
• الرصيد: {balance:.2f} نقطة
• المزادات المنشأة: {total_auctions}
• المزايدات: {total_bids}

اختر الإجراء المطلوب:
    """
        
        bot.edit_message_text(
            balance_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=DREON_balance_menu_inline()
        )
    except:
        bot.send_message(call.message.chat.id, balance_text, reply_markup=DREON_balance_menu_inline())

# دوال الإدارة
def DREON_show_admin_panel(call):
    try:
        stats = DREON_get_bot_stats()
        
        admin_text = f"""
لوحة تحكم الإدارة - {BOT_VERSION}

إحصائيات سريعة:
• إجمالي المستخدمين: {stats['total_users']}
• المزادات النشطة: {stats['active_auctions']}
• في الانتظار: {stats['pending_auctions']}
• إجمالي الرصيد: {stats['total_balance']:.2f}
• إجمالي المزايدات: {stats['total_bids']}
• إجمالي المشاهدات: {stats['total_views']}

اختر الإجراء المطلوب:
    """
        
        bot.edit_message_text(
            admin_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=DREON_admin_panel_inline()
        )
    except:
        bot.send_message(call.message.chat.id, admin_text, reply_markup=DREON_admin_panel_inline())

def DREON_charge_balance_menu(call):
    try:
        bot.edit_message_text(
            "شحن رصيد المستخدمين\n\nاختر مبلغ الشحن أو أدخل مبلغ مخصص:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=DREON_charge_balance_inline()
        )
    except:
        bot.send_message(call.message.chat.id, "اختر مبلغ الشحن أو أدخل مبلغ مخصص:", 
                       reply_markup=DREON_charge_balance_inline())

def DREON_deduct_balance_menu(call):
    try:
        bot.edit_message_text(
            "خصم رصيد المستخدمين\n\nاختر مبلغ الخصم أو أدخل مبلغ مخصص:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=DREON_deduct_balance_inline()
        )
    except:
        bot.send_message(call.message.chat.id, "اختر مبلغ الخصم أو أدخل مبلغ مخصص:", 
                       reply_markup=DREON_deduct_balance_inline())

def DREON_handle_charge_balance(call):
    if call.data == "charge_custom":
        msg = bot.send_message(call.message.chat.id, "أدخل معرف المستخدم:")
        bot.register_next_step_handler(msg, DREON_process_charge_user_id)
    else:
        amount_map = {
            "charge_100": 100,
            "charge_500": 500,
            "charge_1000": 1000,
            "charge_5000": 5000
        }
        amount = amount_map.get(call.data, 0)
        
        msg = bot.send_message(call.message.chat.id, 
                             f"المبلغ: {amount} نقطة\n\nأدخل معرف المستخدم لشحن الرصيد:")
        bot.register_next_step_handler(msg, DREON_process_charge_amount, amount)

def DREON_handle_deduct_balance(call):
    if call.data == "deduct_custom":
        msg = bot.send_message(call.message.chat.id, "أدخل معرف المستخدم:")
        bot.register_next_step_handler(msg, DREON_process_deduct_user_id)
    else:
        amount_map = {
            "deduct_100": 100,
            "deduct_500": 500,
            "deduct_1000": 1000,
            "deduct_5000": 5000
        }
        amount = amount_map.get(call.data, 0)
        
        msg = bot.send_message(call.message.chat.id, 
                             f"المبلغ: {amount} نقطة\n\nأدخل معرف المستخدم لخصم الرصيد:")
        bot.register_next_step_handler(msg, DREON_process_deduct_amount, amount)

def DREON_process_charge_user_id(message):
    try:
        user_id = int(message.text)
        msg = bot.send_message(message.chat.id, "أدخل المبلغ المطلوب شحنه:")
        bot.register_next_step_handler(msg, DREON_process_charge_amount_custom, user_id)
    except ValueError:
        bot.send_message(message.chat.id, "معرف المستخدم غير صالح. الرجاء إدخال رقم.")
        msg = bot.send_message(message.chat.id, "أدخل معرف المستخدم مرة أخرى:")
        bot.register_next_step_handler(msg, DREON_process_charge_user_id)

def DREON_process_charge_amount_custom(message, user_id):
    try:
        amount = float(message.text)
        amount = round(amount, 2)
        
        if amount <= 0:
            bot.send_message(message.chat.id, "المبلغ يجب أن يكون أكبر من الصفر.")
            return
        
        DREON_update_user_balance(user_id, amount)
        DREON_add_transaction(user_id, amount, "شحن", "شحن من الإدارة")
        
        bot.send_message(message.chat.id, f"تم شحن {amount:.2f} نقطة للمستخدم {user_id} بنجاح")
        
        try:
            bot.send_message(user_id, 
                           f"تم شحن رصيد لحسابك\n\nالمبلغ: {amount:.2f} نقطة\nالرصيد الحالي: {DREON_get_user_balance(user_id):.2f} نقطة\n\nمن قبل: الإدارة")
        except:
            pass
            
    except ValueError:
        bot.send_message(message.chat.id, "المبلغ غير صالح. الرجاء إدخال رقم.")

def DREON_process_charge_amount(message, amount, user_id=None):
    if user_id is None:
        try:
            user_id = int(message.text)
        except ValueError:
            bot.send_message(message.chat.id, "معرف المستخدم غير صالح. الرجاء إدخال رقم.")
            return
    
    DREON_update_user_balance(user_id, amount)
    DREON_add_transaction(user_id, amount, "شحن", "شحن من الإدارة")
    
    bot.send_message(message.chat.id, f"تم شحن {amount:.2f} نقطة للمستخدم {user_id} بنجاح")
    
    try:
        bot.send_message(user_id, 
                       f"تم شحن رصيد لحسابك\n\nالمبلغ: {amount:.2f} نقطة\nالرصيد الحالي: {DREON_get_user_balance(user_id):.2f} نقطة\n\nمن قبل: الإدارة")
    except:
        pass

def DREON_process_deduct_user_id(message):
    try:
        user_id = int(message.text)
        msg = bot.send_message(message.chat.id, "أدخل المبلغ المطلوب خصمه:")
        bot.register_next_step_handler(msg, DREON_process_deduct_amount_custom, user_id)
    except ValueError:
        bot.send_message(message.chat.id, "معرف المستخدم غير صالح. الرجاء إدخال رقم.")
        msg = bot.send_message(message.chat.id, "أدخل معرف المستخدم مرة أخرى:")
        bot.register_next_step_handler(msg, DREON_process_deduct_user_id)

def DREON_process_deduct_amount_custom(message, user_id):
    try:
        amount = float(message.text)
        amount = round(amount, 2)
        
        if amount <= 0:
            bot.send_message(message.chat.id, "المبلغ يجب أن يكون أكبر من الصفر.")
            return
        
        user_balance = DREON_get_user_balance(user_id)
        if user_balance < amount:
            bot.send_message(message.chat.id, f"رصيد المستخدم غير كافي. الرصيد الحالي: {user_balance:.2f} نقطة")
            return
        
        DREON_update_user_balance(user_id, -amount)
        DREON_add_transaction(user_id, -amount, "خصم", "خصم من الإدارة")
        
        bot.send_message(message.chat.id, f"تم خصم {amount:.2f} نقطة من المستخدم {user_id} بنجاح")
        
        try:
            bot.send_message(user_id, 
                           f"تم خصم رصيد من حسابك\n\nالمبلغ: {amount:.2f} نقطة\nالرصيد الحالي: {DREON_get_user_balance(user_id):.2f} نقطة\n\nمن قبل: الإدارة")
        except:
            pass
            
    except ValueError:
        bot.send_message(message.chat.id, "المبلغ غير صالح. الرجاء إدخال رقم.")

def DREON_process_deduct_amount(message, amount, user_id=None):
    if user_id is None:
        try:
            user_id = int(message.text)
        except ValueError:
            bot.send_message(message.chat.id, "معرف المستخدم غير صالح. الرجاء إدخال رقم.")
            return
    
    user_balance = DREON_get_user_balance(user_id)
    if user_balance < amount:
        bot.send_message(message.chat.id, f"رصيد المستخدم غير كافي. الرصيد الحالي: {user_balance:.2f} نقطة")
        return
    
    DREON_update_user_balance(user_id, -amount)
    DREON_add_transaction(user_id, -amount, "خصم", "خصم من الإدارة")
    
    bot.send_message(message.chat.id, f"تم خصم {amount:.2f} نقطة من المستخدم {user_id} بنجاح")
    
    try:
        bot.send_message(user_id, 
                       f"تم خصم رصيد من حسابك\n\nالمبلغ: {amount:.2f} نقطة\nالرصيد الحالي: {DREON_get_user_balance(user_id):.2f} نقطة\n\nمن قبل: الإدارة")
    except:
        pass

# دوال إضافية
def DREON_show_auction_categories(call):
    try:
        active_count = DREON_get_active_auctions_count()
        
        bot.edit_message_text(
            f"اختر تصنيف المزادات المطلوب\n\nالمزادات النشطة: {active_count}",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=DREON_auction_categories_inline()
        )
    except:
        bot.send_message(call.message.chat.id, 
                       f"اختر تصنيف المزادات المطلوب\n\nالمزادات النشطة: {active_count}", 
                       reply_markup=DREON_auction_categories_inline())

def DREON_show_auctions_by_category(call):
    category = call.data.replace("category_", "")
    page = 0
    DREON_show_auctions_page(call, category, page)

def DREON_show_auctions_page(call, category, page):
    category_mapping = {
        "all": "جميع المزادات",
        "social_ids": "معرفات السوشيال ميديا",
        "social_accounts": "حسابات السوشيال ميديا",
        "telegram_numbers": "أرقام التليجرام",
        "whatsapp_numbers": "أرقام الواتساب",
        "telegram_channels": "قنوات التليجرام",
        "telegram_groups": "مجموعات التليجرام"
    }
    
    category_name = category_mapping.get(category, "جميع المزادات")
    
    with db_lock:
        conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
        cursor = conn.cursor()
        
        if category == "all":
            cursor.execute('''
                SELECT auction_id, item_type, current_price, end_time, current_bidder, bid_count
                FROM auctions 
                WHERE status = 'active' AND admin_approved = TRUE
                ORDER BY end_time ASC
            ''')
        else:
            cursor.execute('''
                SELECT auction_id, item_type, current_price, end_time, current_bidder, bid_count
                FROM auctions 
                WHERE status = 'active' AND admin_approved = TRUE AND item_type = ?
                ORDER BY end_time ASC
            ''', (category_name,))
        
        auctions = cursor.fetchall()
        conn.close()
    
    active_auctions = []
    for auction in auctions:
        end_time = datetime.fromisoformat(auction[3])
        if (end_time - datetime.now()).total_seconds() > 0:
            active_auctions.append(auction)
    
    if not active_auctions:
        try:
            bot.edit_message_text(
                f"لا توجد مزادات نشطة في تصنيف '{category_name}'\n\nيمكنك تجربة تصنيف آخر أو إنشاء مزاد جديد.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=DREON_auction_categories_inline()
            )
        except:
            bot.send_message(call.message.chat.id, 
                           f"لا توجد مزادات نشطة في تصنيف '{category_name}'", 
                           reply_markup=DREON_auction_categories_inline())
        return
    
    try:
        bot.edit_message_text(
            f"المزادات النشطة - {category_name}\n\nإجمالي المزادات: {len(active_auctions)}\nاختر مزاد للمزايدة:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=DREON_auctions_list_inline(active_auctions, category, page)
        )
    except:
        bot.send_message(call.message.chat.id, 
                       f"المزادات النشطة - {category_name}\n\nإجمالي المزادات: {len(active_auctions)}", 
                       reply_markup=DREON_auctions_list_inline(active_auctions, category, page))

def DREON_handle_page_navigation(call):
    data_parts = call.data.split('_')
    if len(data_parts) < 3:
        return
    
    category = data_parts[1]
    page = int(data_parts[2])
    DREON_show_auctions_page(call, category, page)

def DREON_create_auction_start(call):
    try:
        bot.edit_message_text(
            "اختر نوع المزاد الذي تريد إنشاءه:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=DREON_auction_types_inline()
        )
    except:
        bot.send_message(call.message.chat.id, "اختر نوع المزاد الذي تريد إنشاءه:", 
                       reply_markup=DREON_auction_types_inline())

def DREON_handle_auction_type_selection(call):
    auction_type = call.data.replace("type_", "")
    
    type_mapping = {
        "social_ids": "معرفات السوشيال ميديا",
        "social_accounts": "حسابات السوشيال ميديا",
        "telegram_numbers": "أرقام التليجرام",
        "whatsapp_numbers": "أرقام الواتساب",
        "telegram_channels": "قنوات التليجرام",
        "telegram_groups": "مجموعات التليجرام"
    }
    
    selected_type = type_mapping.get(auction_type, auction_type)
    
    msg = bot.send_message(call.message.chat.id, 
                          f"تم اختيار: {selected_type}\n\nالآن أدخل وصف المزاد (مثال: معرف انستغرام مميز):")
    bot.register_next_step_handler(msg, DREON_process_auction_description, selected_type)

def DREON_process_auction_description(message, item_type):
    description = message.text.strip()
    
    if len(description) < 5:
        bot.send_message(message.chat.id, "الوصف قصير جداً. الرجاء إدخال وصف مفصل.")
        msg = bot.send_message(message.chat.id, "أدخل وصف المزاد مرة أخرى:")
        bot.register_next_step_handler(msg, DREON_process_auction_description, item_type)
        return
    
    msg = bot.send_message(message.chat.id, "أدخل سعر البدء (النقاط):")
    bot.register_next_step_handler(msg, DREON_process_start_price, item_type, description)

def DREON_process_start_price(message, item_type, description):
    try:
        start_price = float(message.text)
        start_price = round(start_price, 2)
        
        if start_price < 1:
            bot.send_message(message.chat.id, "سعر البدء يجب أن يكون على الأقل 1 نقطة")
            msg = bot.send_message(message.chat.id, "أدخل سعر البدء مرة أخرى:")
            bot.register_next_step_handler(msg, DREON_process_start_price, item_type, description)
            return
            
    except ValueError:
        bot.send_message(message.chat.id, "السعر غير صالح. الرجاء إدخال رقم.")
        msg = bot.send_message(message.chat.id, "أدخل سعر البدء مرة أخرى:")
        bot.register_next_step_handler(msg, DREON_process_start_price, item_type, description)
        return
    
    commission = (start_price * COMMISSION_RATE) / 100
    user_id = message.from_user.id
    user_balance = DREON_get_user_balance(user_id)
    
    if user_balance < commission:
        bot.send_message(message.chat.id, 
                       f"رصيدك غير كافي\n\nتحتاج {commission:.2f} نقطة لبدء المزاد\nرصيدك الحالي: {user_balance:.2f} نقطة",
                       reply_markup=DREON_main_menu_inline(user_id))
        return
    
    DREON_update_user_balance(user_id, -commission)
    DREON_add_transaction(user_id, -commission, "عمولة", f"عمولة إنشاء مزاد - {item_type}")
    
    auction_id = DREON_generate_auction_id()
    end_time = datetime.now() + timedelta(days=7)
    
    with db_lock:
        conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO auctions (auction_id, seller_id, item_type, item_description, start_price, current_price, status, created_at, end_time)
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
        ''', (auction_id, user_id, item_type, description, start_price, start_price, datetime.now().isoformat(), end_time.isoformat()))
        
        cursor.execute('UPDATE users SET total_auctions = total_auctions + 1 WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()
    
    DREON_notify_admins_new_auction(auction_id, item_type, user_id, start_price, description, commission)
    
    success_msg = f"""
تم إنشاء المزاد بنجاح

رقم المزاد: {auction_id}
نوع المزاد: {item_type}
سعر البدء: {start_price:.2f} نقطة
العمولة المخصومة: {commission:.2f} نقطة
مدة المزاد: 7 أيام

في انتظار موافقة الإدارة
    """
    bot.send_message(message.chat.id, success_msg, reply_markup=DREON_main_menu_inline(user_id))

def DREON_notify_admins_new_auction(auction_id, auction_type, seller_id, start_price, description, commission):
    for admin_id in ADMIN_IDS:
        try:
            approval_text = f"""
مزاد جديد يحتاج الموافقة

رقم المزاد: {auction_id}
النوع: {auction_type}
البائع: {seller_id}
سعر البدء: {start_price:.2f} نقطة
الوصف: {description[:100]}...
العمولة المخصومة: {commission:.2f} نقطة
            """
            bot.send_message(admin_id, approval_text, reply_markup=DREON_admin_auction_actions_inline(auction_id))
        except Exception as e:
            print(f"فشل في إرسال إشعار للإدمن {admin_id}: {e}")

def DREON_show_my_auctions(call):
    try:
        user_id = call.from_user.id
        
        with db_lock:
            conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT auction_id, item_type, current_price, status, admin_approved, end_time
                FROM auctions 
                WHERE seller_id = ?
                ORDER BY created_at DESC
                LIMIT 10
            ''', (user_id,))
            my_auctions = cursor.fetchall()
            conn.close()
        
        if not my_auctions:
            bot.edit_message_text(
                "لم تقم بإنشاء أي مزادات بعد\n\nاستخدم زر 'إنشاء مزاد جديد' لبدء أول مزاد لك.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=DREON_main_menu_inline(user_id)
            )
            return
        
        total_auctions = len(my_auctions)
        active_auctions = sum(1 for a in my_auctions if a[3] == 'active' and a[4])
        pending_auctions = sum(1 for a in my_auctions if not a[4])
        sold_auctions = sum(1 for a in my_auctions if a[3] == 'sold')
        
        auctions_text = f"""
مزاداتك المنشأة

الإحصائيات:
• الإجمالي: {total_auctions}
• النشطة: {active_auctions}
• قيد المراجعة: {pending_auctions}
• المباعة: {sold_auctions}

قائمة المزادات:
"""
        
        keyboard = telebot.types.InlineKeyboardMarkup()
        
        for auction in my_auctions[:8]:
            auction_id, item_type, current_price, status, admin_approved, end_time = auction
            end_time = datetime.fromisoformat(end_time)
            time_left = end_time - datetime.now()
            
            if status == "sold":
                status_text = "مباع"
            elif status == "active" and admin_approved:
                status_text = "نشط"
            elif not admin_approved:
                status_text = "قيد المراجعة"
            else:
                status_text = "منتهي"
            
            short_type = item_type[:15] + "..." if len(item_type) > 15 else item_type
            
            button_text = f"{short_type} - {current_price:.0f}"
            keyboard.row(
                telebot.types.InlineKeyboardButton(button_text, callback_data=f"view_auction_{auction_id}")
            )
        
        keyboard.row(
            telebot.types.InlineKeyboardButton("إنشاء مزاد جديد", callback_data="create_auction"),
            telebot.types.InlineKeyboardButton("تحديث", callback_data="my_auctions")
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton("الرئيسية", callback_data="main_menu")
        )
        
        bot.edit_message_text(
            auctions_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"خطأ في show_my_auctions: {e}")
        bot.send_message(call.message.chat.id, "حدث خطأ في عرض المزادات.")

def DREON_show_my_active_bids(call):
    try:
        user_id = call.from_user.id
        active_bids = DREON_get_user_active_bids(user_id)
        
        if not active_bids:
            bot.edit_message_text(
                "لا توجد مزايدات نشطة\n\nلم تقم بالمزايدة على أي مزاد نشط حالياً.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=DREON_main_menu_inline(user_id)
            )
            return
        
        bids_text = f"""
مزايداتك النشطة

إجمالي المزايدات النشطة: {len(active_bids)}

قائمة المزايدات:
"""
        
        keyboard = telebot.types.InlineKeyboardMarkup()
        
        for i, bid in enumerate(active_bids, 1):
            auction_id, item_type, current_price, end_time = bid
            end_time = datetime.fromisoformat(end_time)
            time_left = end_time - datetime.now()
            
            short_type = item_type[:18] + "..." if len(item_type) > 18 else item_type
            
            bids_text += f"\n{i}. {short_type}\n   {auction_id} - {current_price:.2f} - {time_left.days} أيام\n"
            
            button_text = f"{short_type} - {current_price:.0f}"
            keyboard.row(
                telebot.types.InlineKeyboardButton(button_text, callback_data=f"view_auction_{auction_id}")
            )
        
        keyboard.row(
            telebot.types.InlineKeyboardButton("تحديث", callback_data="my_active_bids"),
            telebot.types.InlineKeyboardButton("الرئيسية", callback_data="main_menu")
        )
        
        bot.edit_message_text(
            bids_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"خطأ في show_my_active_bids: {e}")
        bot.send_message(call.message.chat.id, "حدث خطأ في عرض المزايدات.")

def DREON_show_my_favorites(call):
    try:
        user_id = call.from_user.id
        favorites = DREON_get_user_favorites(user_id)
        
        if not favorites:
            bot.edit_message_text(
                "لا توجد عناصر في المفضلة\n\nيمكنك إضافة مزادات للمفضلة من خلال تفاصيل المزاد.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=DREON_main_menu_inline(user_id)
            )
            return
        
        favorites_text = f"""
المفضلة

إجمالي العناصر: {len(favorites)}

قائمة المفضلة:
"""
        
        keyboard = telebot.types.InlineKeyboardMarkup()
        
        for i, fav in enumerate(favorites, 1):
            auction_id, item_type, current_price, end_time = fav
            end_time = datetime.fromisoformat(end_time)
            time_left = end_time - datetime.now()
            
            short_type = item_type[:18] + "..." if len(item_type) > 18 else item_type
            
            favorites_text += f"\n{i}. {short_type}\n   {auction_id} - {current_price:.2f} - {time_left.days} أيام\n"
            
            button_text = f"{short_type} - {current_price:.0f}"
            keyboard.row(
                telebot.types.InlineKeyboardButton(button_text, callback_data=f"view_auction_{auction_id}")
            )
        
        keyboard.row(
            telebot.types.InlineKeyboardButton("تحديث", callback_data="my_favorites"),
            telebot.types.InlineKeyboardButton("الرئيسية", callback_data="main_menu")
        )
        
        bot.edit_message_text(
            favorites_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"خطأ في show_my_favorites: {e}")
        bot.send_message(call.message.chat.id, "حدث خطأ في عرض المفضلة.")

def DREON_handle_favorite_toggle(call):
    try:
        auction_id = call.data.replace("favorite_", "")
        user_id = call.from_user.id
        
        if DREON_is_favorite(user_id, auction_id):
            DREON_remove_from_favorites(user_id, auction_id)
            bot.answer_callback_query(call.id, "تمت الإزالة من المفضلة")
        else:
            if DREON_add_to_favorites(user_id, auction_id):
                bot.answer_callback_query(call.id, "تمت الإضافة إلى المفضلة")
            else:
                bot.answer_callback_query(call.id, "فشل في الإضافة للمفضلة")
        
        DREON_show_auction_detail(call)
    except Exception as e:
        print(f"خطأ في handle_favorite_toggle: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في تعديل المفضلة")

def DREON_show_pending_auctions(call):
    try:
        with db_lock:
            conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT auction_id, item_type, seller_id, start_price, item_description, created_at
                FROM auctions 
                WHERE admin_approved = FALSE AND status = 'pending'
                ORDER BY created_at DESC
                LIMIT 10
            ''')
            auctions = cursor.fetchall()
            conn.close()
        
        if not auctions:
            bot.edit_message_text(
                "لا توجد مزادات في انتظار الموافقة",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=DREON_admin_panel_inline()
            )
            return
        
        if len(auctions) == 1:
            auction = auctions[0]
            DREON_show_single_pending_auction(call, auction)
        else:
            DREON_show_pending_auctions_list(call, auctions)
    except Exception as e:
        print(f"خطأ في show_pending_auctions: {e}")
        bot.send_message(call.message.chat.id, "حدث خطأ في عرض المزادات المنتظرة.")

def DREON_show_single_pending_auction(call, auction):
    try:
        auction_id, item_type, seller_id, start_price, description, created_at = auction
        created_time = datetime.fromisoformat(created_at)
        
        auction_text = f"""
مزاد منتظر الموافقة

رقم المزاد: {auction_id}
النوع: {item_type}
البائع: {seller_id}
سعر البدء: {start_price:.2f} نقطة
الوصف: {description[:100]}{'...' if len(description) > 100 else ''}
وقت الإنشاء: {created_time.strftime('%Y-%m-%d %H:%M')}
        """
        
        bot.edit_message_text(
            auction_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=DREON_admin_auction_actions_inline(auction_id)
        )
    except:
        bot.send_message(call.message.chat.id, auction_text, reply_markup=DREON_admin_auction_actions_inline(auction_id))

def DREON_show_pending_auctions_list(call, auctions):
    try:
        auctions_text = "قائمة المزادات المنتظرة\n\n"
        
        for i, auction in enumerate(auctions, 1):
            auction_id, item_type, seller_id, start_price, description, created_at = auction
            short_desc = description[:50] + "..." if len(description) > 50 else description
            auctions_text += f"{i}. {auction_id} - {item_type} - {start_price:.2f} نقطة\n"
        
        keyboard = telebot.types.InlineKeyboardMarkup()
        
        for auction in auctions[:5]:
            auction_id, item_type, _, start_price, _, _ = auction
            button_text = f"{item_type} - {start_price:.0f}"
            keyboard.row(
                telebot.types.InlineKeyboardButton(button_text, callback_data=f"details_{auction_id}")
            )
        
        keyboard.row(
            telebot.types.InlineKeyboardButton("تحديث", callback_data="pending_auctions"),
            telebot.types.InlineKeyboardButton("الرئيسية", callback_data="admin_panel")
        )
        
        bot.edit_message_text(
            auctions_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except:
        bot.send_message(call.message.chat.id, auctions_text, reply_markup=keyboard)

def DREON_handle_auction_approval(call):
    try:
        auction_id = call.data.replace("approve_", "")
        
        with db_lock:
            conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE auctions 
                SET admin_approved = TRUE, status = 'active' 
                WHERE auction_id = ?
            ''', (auction_id,))
            
            cursor.execute('SELECT seller_id, item_type FROM auctions WHERE auction_id = ?', (auction_id,))
            result = cursor.fetchone()
            
            conn.commit()
            conn.close()
        
        if result:
            seller_id, item_type = result
            try:
                bot.send_message(seller_id, 
                               f"تمت الموافقة على مزادك\n\nرقم المزاد: {auction_id}\nالنوع: {item_type}\n\nتم نشره بنجاح ويمكن للمستخدمين المزايدة عليه الآن.")
            except:
                pass
        
        bot.answer_callback_query(call.id, "تمت الموافقة على المزاد")
        DREON_show_pending_auctions(call)
    except Exception as e:
        print(f"خطأ في handle_auction_approval: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في الموافقة على المزاد")

def DREON_handle_auction_rejection(call):
    try:
        auction_id = call.data.replace("reject_", "")
        
        with db_lock:
            conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute('SELECT seller_id, start_price FROM auctions WHERE auction_id = ?', (auction_id,))
            result = cursor.fetchone()
            
            if result:
                seller_id, start_price = result
                commission = (start_price * COMMISSION_RATE) / 100
                commission = round(commission, 2)
                
                DREON_update_user_balance(seller_id, commission)
                DREON_add_transaction(seller_id, commission, "استرجاع", f"استرجاع عمولة مزاد مرفوض - {auction_id}")
            
            cursor.execute('DELETE FROM auctions WHERE auction_id = ?', (auction_id,))
            conn.commit()
            conn.close()
        
        if result:
            seller_id, start_price = result
            try:
                bot.send_message(seller_id, 
                               f"تم رفض مزادك\n\nرقم المزاد: {auction_id}\nتم استرجاع العمولة البالغة {commission:.2f} نقطة لحسابك.\n\nالرجاء التحقق من شروط إنشاء المزادات والمحاولة مرة أخرى.")
            except:
                pass
        
        bot.answer_callback_query(call.id, "تم رفض المزاد")
        DREON_show_pending_auctions(call)
    except Exception as e:
        print(f"خطأ في handle_auction_rejection: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في رفض المزاد")

def DREON_show_bot_stats(call):
    try:
        stats = DREON_get_bot_stats()
        
        with db_lock:
            conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute('SELECT SUM(current_price) FROM auctions WHERE status = "active"')
            total_active_value = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT SUM(sold_price) FROM auctions WHERE status = "sold"')
            total_sold_value = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT COUNT(*) FROM transactions')
            total_transactions = cursor.fetchone()[0]
            
            conn.close()
        
        stats_text = f"""
إحصائيات البوت - {BOT_VERSION}

المستخدمين:
• إجمالي المستخدمين: {stats['total_users']:,}
• إجمالي الرصيد: {stats['total_balance']:,.2f} نقطة

المزادات:
• النشطة: {stats['active_auctions']}
• المباعة: {stats['sold_auctions']}
• قيد المراجعة: {stats['pending_auctions']}

القيمة الإجمالية:
• قيمة المزادات النشطة: {total_active_value:,.2f} نقطة
• إجمالي المبيعات: {total_sold_value:,.2f} نقطة

النشاط:
• إجمالي المزايدات: {stats['total_bids']}
• إجمالي المعاملات: {total_transactions}
• إجمالي المشاهدات: {stats['total_views']}
    """
        
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton("تحديث الإحصائيات", callback_data="bot_stats"),
            telebot.types.InlineKeyboardButton("لوحة التحكم", callback_data="admin_panel")
        )
        
        bot.edit_message_text(
            stats_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"خطأ في show_bot_stats: {e}")
        bot.send_message(call.message.chat.id, "حدث خطأ في عرض إحصائيات البوت.")

def DREON_manage_users(call):
    try:
        stats = DREON_get_bot_stats()
        
        users_text = f"""
إدارة المستخدمين - {BOT_VERSION}

الإحصائيات:
• إجمالي المستخدمين: {stats['total_users']}
• إجمالي الرصيد: {stats['total_balance']:.2f} نقطة

لشحن رصيد مستخدم، استخدم خيار "شحن رصيد" في لوحة الإدارة
    """
        
        bot.edit_message_text(
            users_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=DREON_admin_panel_inline()
        )
    except:
        bot.send_message(call.message.chat.id, users_text, reply_markup=DREON_admin_panel_inline())

def DREON_show_ended_auctions(call):
    try:
        with db_lock:
            conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT auction_id, item_type, current_price, end_time, seller_id, current_bidder
                FROM auctions 
                WHERE status = 'active' AND admin_approved = TRUE AND end_time < ?
                ORDER BY end_time DESC
                LIMIT 10
            ''', (datetime.now().isoformat(),))
            auctions = cursor.fetchall()
            conn.close()
        
        if not auctions:
            bot.edit_message_text(
                "لا توجد مزادات منتهية تحتاج إكمال بيع",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=DREON_admin_panel_inline()
            )
            return
        
        if len(auctions) == 1:
            auction = auctions[0]
            DREON_show_single_ended_auction(call, auction)
        else:
            DREON_show_ended_auctions_list(call, auctions)
    except Exception as e:
        print(f"خطأ في show_ended_auctions: {e}")
        bot.send_message(call.message.chat.id, "حدث خطأ في عرض المزادات المنتهية.")

def DREON_show_single_ended_auction(call, auction):
    try:
        auction_id, item_type, current_price, end_time, seller_id, current_bidder = auction
        end_time = datetime.fromisoformat(end_time)
        
        auction_text = f"""
مزاد منتهي

رقم المزاد: {auction_id}
النوع: {item_type}
السعر النهائي: {current_price:.2f} نقطة
البائع: {seller_id}
المشتري: {current_bidder if current_bidder else 'لا يوجد'}
وقت الانتهاء: {end_time.strftime('%Y-%m-%d %H:%M')}
        """
        
        bot.edit_message_text(
            auction_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=DREON_ended_auctions_inline(auction_id)
        )
    except:
        bot.send_message(call.message.chat.id, auction_text, reply_markup=DREON_ended_auctions_inline(auction_id))

def DREON_show_ended_auctions_list(call, auctions):
    try:
        auctions_text = "قائمة المزادات المنتهية\n\n"
        
        for i, auction in enumerate(auctions, 1):
            auction_id, item_type, current_price, end_time, seller_id, current_bidder = auction
            end_time = datetime.fromisoformat(end_time)
            time_str = end_time.strftime('%m/%d %H:%M')
            auctions_text += f"{i}. {auction_id} - {item_type} - {current_price:.2f} نقطة - {time_str}\n"
        
        keyboard = telebot.types.InlineKeyboardMarkup()
        
        for auction in auctions[:5]:
            auction_id, item_type, current_price, _, _, _ = auction
            button_text = f"{item_type} - {current_price:.0f}"
            keyboard.row(
                telebot.types.InlineKeyboardButton(button_text, callback_data=f"details_{auction_id}")
            )
        
        keyboard.row(
            telebot.types.InlineKeyboardButton("تحديث", callback_data="ended_auctions"),
            telebot.types.InlineKeyboardButton("الرئيسية", callback_data="admin_panel")
        )
        
        bot.edit_message_text(
            auctions_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except:
        bot.send_message(call.message.chat.id, auctions_text, reply_markup=keyboard)

def DREON_handle_complete_sale(call):
    try:
        auction_id = call.data.replace("complete_sale_", "")
        DREON_complete_auction_sale(auction_id)
        
        bot.answer_callback_query(call.id, "تم إكمال عملية البيع بنجاح")
        DREON_show_ended_auctions(call)
    except Exception as e:
        print(f"خطأ في handle_complete_sale: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ في إكمال البيع")

def DREON_show_auction_details(call):
    try:
        auction_id = call.data.replace("details_", "")
        auction = DREON_get_auction_details(auction_id)
        
        if not auction:
            bot.answer_callback_query(call.id, "المزاد غير موجود")
            return
        
        auction_text = f"""
تفاصيل كاملة للمزاد

رقم المزاد: {auction[0]}
البائع: {auction[1]}
النوع: {auction[2]}
الوصف: {auction[3]}
سعر البدء: {auction[4]:.2f} نقطة
السعر الحالي: {auction[5]:.2f} نقطة
المزايد الحالي: {auction[6] if auction[6] else 'لا يوجد'}
الحالة: {auction[7]}
وقت الإنشاء: {datetime.fromisoformat(auction[8]).strftime('%Y-%m-%d %H:%M')}
وقت الانتهاء: {datetime.fromisoformat(auction[9]).strftime('%Y-%m-%d %H:%M')}
موافقة الإدارة: {'نعم' if auction[10] else 'لا'}
عدد المزايدات: {auction[13]}
عدد المشاهدات: {auction[14]}
    """
        
        if auction[11]:
            auction_text += f"\nسعر البيع: {auction[11]:.2f} نقطة"
        if auction[12]:
            auction_text += f"\nالمشتري: {auction[12]}"
        
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            auction_text,
            call.message.chat.id,
            call.message.message_id
        )
    except:
        bot.send_message(call.message.chat.id, auction_text)

def DREON_show_bid_history(call):
    try:
        auction_id = call.data.replace("bid_history_", "")
        bids = DREON_get_bid_history(auction_id, 15)
        
        if not bids:
            bot.answer_callback_query(call.id, "لا توجد مزايدات بعد")
            return
        
        auction = DREON_get_auction_details(auction_id)
        if not auction:
            bot.answer_callback_query(call.id, "المزاد غير موجود")
            return
        
        history_text = f"""
سجل المزايدات

رقم المزاد: {auction_id}
النوع: {auction[2]}
السعر الحالي: {auction[5]:.2f} نقطة

آخر {len(bids)} مزايدة:
"""
        
        for i, bid in enumerate(bids, 1):
            bidder_id, bid_amount, bid_time = bid
            bid_time = datetime.fromisoformat(bid_time)
            time_str = bid_time.strftime('%m/%d %H:%M')
            
            history_text += f"\n{i}. المستخدم {bidder_id}: {bid_amount:.2f} نقطة - الوقت: {time_str}"
        
        total_bids = len(bids)
        highest_bid = bids[0][1] if bids else 0
        average_bid = sum(bid[1] for bid in bids) / total_bids if bids else 0
        
        history_text += f"\n\nالإحصائيات:"
        history_text += f"\n• إجمالي المزايدات: {total_bids}"
        history_text += f"\n• أعلى مزايدة: {highest_bid:.2f} نقطة"
        history_text += f"\n• متوسط المزايدات: {average_bid:.2f} نقطة"
        
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            history_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=DREON_bid_history_inline(auction_id)
        )
    except:
        bot.send_message(call.message.chat.id, history_text, reply_markup=DREON_bid_history_inline(auction_id))

def DREON_start_broadcast(call):
    try:
        msg = bot.send_message(call.message.chat.id, 
                              "إرسال إعلان عام\n\nأدخل نص الإعلان الذي تريد إرساله لجميع المستخدمين:")
        bot.register_next_step_handler(msg, DREON_process_broadcast_message)
    except Exception as e:
        print(f"خطأ في start_broadcast: {e}")
        bot.send_message(call.message.chat.id, "حدث خطأ في بدء الإعلان.")

def DREON_process_broadcast_message(message):
    try:
        broadcast_text = message.text
        user_id = message.from_user.id
        
        if user_id not in ADMIN_IDS:
            bot.send_message(message.chat.id, "غير مسموح لك بهذا الإجراء")
            return
        
        with db_lock:
            conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM users')
            users = cursor.fetchall()
            conn.close()
        
        sent_count = 0
        failed_count = 0
        
        bot.send_message(message.chat.id, f"بدء إرسال الإعلان لـ {len(users)} مستخدم...")
        
        for user in users:
            try:
                bot.send_message(user[0], f"إعلان عام من الإدارة\n\n{broadcast_text}")
                sent_count += 1
                time.sleep(0.1)
            except:
                failed_count += 1
        
        bot.send_message(message.chat.id, 
                       f"تم إرسال الإعلان\n\nتم الإرسال بنجاح: {sent_count}\nفشل في الإرسال: {failed_count}")
    except Exception as e:
        print(f"خطأ في process_broadcast_message: {e}")
        bot.send_message(message.chat.id, "حدث خطأ في إرسال الإعلان.")

# نظام المهام الدورية
def DREON_check_ending_auctions():
    while True:
        try:
            with db_lock:
                conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
                cursor = conn.cursor()
                
                one_hour_later = datetime.now() + timedelta(hours=1)
                cursor.execute('''
                    SELECT auction_id, item_type, current_price, current_bidder, seller_id, end_time
                    FROM auctions 
                    WHERE status = 'active' AND admin_approved = TRUE 
                    AND end_time BETWEEN ? AND ?
                ''', (datetime.now().isoformat(), one_hour_later.isoformat()))
                
                ending_auctions = cursor.fetchall()
                conn.close()
            
            for auction in ending_auctions:
                auction_id, item_type, current_price, current_bidder, seller_id, end_time = auction
                end_time = datetime.fromisoformat(end_time)
                time_left = end_time - datetime.now()
                minutes_left = int(time_left.total_seconds() // 60)
                
                if minutes_left <= 60:
                    try:
                        bot.send_message(
                            seller_id,
                            f"تنبيه انتهاء المزاد\n\nمزادك {auction_id} سينتهي خلال {minutes_left} دقيقة\nالسعر الحالي: {current_price:.2f} نقطة\nالمنتج: {item_type}\n\nتأكد من متابعة المزاد حتى النهاية!"
                        )
                    except:
                        pass
                    
                    if current_bidder:
                        try:
                            bot.send_message(
                                current_bidder,
                                f"تنبيه انتهاء المزاد\n\nالمزاد {auction_id} الذي تتصدره سينتهي خلال {minutes_left} دقيقة\nمزايدتك الحالية: {current_price:.2f} نقطة\nالمنتج: {item_type}\n\nقد تحتاج للمزايدة مرة أخرى للحفاظ على موقعك!"
                            )
                        except:
                            pass
            
            time.sleep(60)
            
        except Exception as e:
            print(f"خطأ في المهام الدورية: {e}")
            time.sleep(60)

def DREON_complete_ended_auctions():
    while True:
        try:
            with db_lock:
                conn = sqlite3.connect('auction_bot.db', check_same_thread=False)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT auction_id FROM auctions 
                    WHERE status = 'active' AND admin_approved = TRUE AND end_time < ?
                ''', (datetime.now().isoformat(),))
                
                ended_auctions = cursor.fetchall()
                conn.close()
            
            for auction in ended_auctions:
                auction_id = auction[0]
                DREON_complete_auction_sale(auction_id)
            
            time.sleep(30)
            
        except Exception as e:
            print(f"خطأ في إكمال المزادات المنتهية: {e}")
            time.sleep(30)

def DREON_start_periodic_tasks():
    tasks = [
        DREON_check_ending_auctions,
        DREON_complete_ended_auctions
    ]
    
    for task in tasks:
        thread = threading.Thread(target=task, daemon=True)
        thread.start()

DREON_start_periodic_tasks()

print(f"بدء تشغيل DREON {BOT_VERSION}...")
print("تحميل النظام والتحقق من المزادات...")
print("بدء المهام الدورية...")

try:
    bot.infinity_polling()
except Exception as e:
    print(f"خطأ في تشغيل البوت: {e}")