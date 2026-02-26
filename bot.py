import logging
import asyncio
import sys

# 只在 Windows 上设置 SelectorEventLoopPolicy（Render 是 Linux，不会执行）
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# ================== 配置部分 ==================
TOKEN = '8645061491:AAG_TY-z5AxPlfwufyUk3p-RL0Wycmb2vG8'
ADMIN_ID = 7951568814

# 商品列表（用于添加卡密按钮）
PRODUCTS = ['1日体验', '体验套餐', '月度套餐', '半年套餐', '年度套餐']

# 商品卡密（内存存储，重启丢失，建议后期改用文件或数据库）
CARDS = {
    '1日体验': ['账号:密码示例1', '账号:密码示例2'],
    '体验套餐': [],
    '月度套餐': [],
    '半年套餐': [],
    '年度套餐': []
}

# 支付方式与价格
PAYMENT_METHODS = {
    'usdt': {
        'name': 'USDT (TRC-20)',
        'address': "TM7mEQavbxtYKFKJq3VAm3oh49V7jLAwD9",
        'prices': {
            '1日体验': 11.64,
            '体验套餐': 56.64,
            '月度套餐': 86.64,
            '半年套餐': 386.64,
            '年度套餐': 566.64
        }
    },
    'wechat': {
        'name': '微信支付',
        'qr_photo': 'wechat_qr.png',
        'prices': {
            '1日体验': 11.64,
            '体验套餐': 56.64,
            '月度套餐': 86.64,
            '半年套餐': 386.64,
            '年度套餐': 566.64
        }
    },
    'alipay': {
        'name': '支付宝',
        'qr_photo': 'alipay_qr.png',
        'prices': {
            '1日体验': 11.64,
            '体验套餐': 56.64,
            '月度套餐': 86.64,
            '半年套餐': 386.64,
            '年度套餐': 566.64
        }
    }
}

# 客服联系方式（请修改成你的真实信息）
CUSTOMER_SERVICE = {
    'text': "客服联系方式：\n@doubao1998\n或直接私聊我处理问题",
    'link': "https://t.me/doubao1998"
}
# ==============================================

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

PENDING_PAYMENTS = {}
PENDING_ADD_CARD = {}  # 管理员正在添加的商品 {user_id: '商品名'}

# 主菜单
def get_main_menu(is_admin=False):
    keyboard = [
        [InlineKeyboardButton("查看套餐", callback_data="show_packages")],
        [InlineKeyboardButton("帮助 / 说明", callback_data="help")],
        [InlineKeyboardButton("联系客服", callback_data="contact_support")],
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton("添加卡密", callback_data="admin_add_card")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    is_admin = update.effective_user.id == ADMIN_ID
    reply_markup = get_main_menu(is_admin)
    await update.message.reply_text("欢迎使用发卡机器人！请选择功能：", reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "帮助说明：\n"
        "1. 点击“查看套餐”浏览商品\n"
        "2. 选择套餐 → 选支付方式 → 支付后回复“已支付 订单号”确认\n"
        "3. 如卡密无效或有问题，请联系客服"
    )
    keyboard = [[InlineKeyboardButton("返回主菜单", callback_data="back_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    is_admin = user_id == ADMIN_ID

    if data == "show_packages":
        keyboard = [
            [InlineKeyboardButton("✨1日体验 | ¥11.64 | 1天 | 1GB", callback_data="buy_1日体验")],
            [InlineKeyboardButton("🔥体验套餐 | ¥56.64 | 30天 | 30GB", callback_data="buy_体验套餐")],
            [InlineKeyboardButton("🔥月度套餐 | ¥86.64 | 30天 | 75GB", callback_data="buy_月度套餐")],
            [InlineKeyboardButton("👑半年套餐 | ¥386.64 | 210天 | 540GB", callback_data="buy_半年套餐")],
            [InlineKeyboardButton("👑年度套餐 | ¥566.64 | 420天 | 1200GB", callback_data="buy_年度套餐")],
            [InlineKeyboardButton("← 返回主菜单", callback_data="back_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("请选择你的套餐：", reply_markup=reply_markup)
        return

    if data == "help":
        await help_command(update, context)
        return

    if data == "contact_support":
        text = CUSTOMER_SERVICE['text']
        keyboard = [
            [InlineKeyboardButton("联系客服", url=CUSTOMER_SERVICE['link'])],
            [InlineKeyboardButton("返回主菜单", callback_data="back_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(text, reply_markup=reply_markup)
        return

    if data == "admin_add_card" and is_admin:
        keyboard = []
        for product in PRODUCTS:
            keyboard.append([InlineKeyboardButton(product, callback_data=f"add_card_{product}")])
        keyboard.append([InlineKeyboardButton("← 返回主菜单", callback_data="back_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("请选择要添加卡密的商品：", reply_markup=reply_markup)
        return

    if data.startswith("add_card_") and is_admin:
        category = data[9:]
        PENDING_ADD_CARD[user_id] = category
        text = f"正在为 **{category}** 添加卡密\n请直接回复卡密内容（例如：用户名:abc 密码:123 有效期:1天）\n\n回复后自动添加。"
        keyboard = [[InlineKeyboardButton("取消添加", callback_data="cancel_add_card")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        return

    if data == "cancel_add_card" and is_admin:
        if user_id in PENDING_ADD_CARD:
            del PENDING_ADD_CARD[user_id]
        reply_markup = get_main_menu(is_admin)
        await query.message.edit_text("已取消添加卡密。请选择功能：", reply_markup=reply_markup)
        return

    if data == "back_main":
        reply_markup = get_main_menu(is_admin)
        await query.message.edit_text("欢迎回来！请选择功能：", reply_markup=reply_markup)
        return

    # 购买逻辑
    if data.startswith('buy_'):
        category = data[4:]
        if category not in CARDS or not CARDS[category]:
            await query.message.reply_text(f"{category} 已售罄或不存在")
            return
        keyboard = []
        for method_key, method in PAYMENT_METHODS.items():
            base_amount = method['prices'].get(category, 0)
            if method_key == 'usdt':
                display_amount = base_amount / 7
                currency_symbol = '$'
                btn_text = f"USDT (TRC-20) - {currency_symbol}{display_amount:.2f}"
            else:
                display_amount = base_amount
                currency_symbol = '¥'
                btn_text = f"{method['name']} - {currency_symbol}{display_amount:.2f}"
            callback_data = f"pay_{method_key}_{category}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=callback_data)])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(f"请选择支付方式（{category}）：", reply_markup=reply_markup)
        return

    if data.startswith('pay_'):
        parts = data.split('_', 2)
        method_key = parts[1]
        category = parts[2]
        method = PAYMENT_METHODS[method_key]
        base_amount = method['prices'].get(category, 0)
        order_id = f"ord-{user_id}-{category[:10]}"
        PENDING_PAYMENTS[user_id] = {
            'category': category,
            'method': method_key,
            'amount': base_amount,
            'order_id': order_id
        }
        if method_key == 'usdt':
            display_amount = base_amount / 7
            text = (
                f"请支付 **${display_amount:.2f} USDT** (TRC-20)\n"
                f"地址：`{method['address']}`\n"
                f"备注（必填）：{order_id}\n\n"
                f"支付后回复：已支付 {order_id}"
            )
            await query.message.reply_text(text, parse_mode='Markdown')
        else:
            display_amount = base_amount
            photo = method['qr_photo']
            caption = (
                f"请使用 {method['name']} 扫码支付 **¥{display_amount:.2f}**\n"
                f"备注/附言（可选）：{order_id}\n\n"
                f"支付后回复：已支付 {order_id}"
            )
            if photo.startswith('http'):
                await query.message.reply_photo(photo=photo, caption=caption)
            else:
                await query.message.reply_photo(photo=open(photo, 'rb'), caption=caption)
        return

    if data == 'soldout':
        await query.answer("已售罄～", show_alert=True)

async def handle_add_card_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in PENDING_ADD_CARD or user_id != ADMIN_ID:
        return
    category = PENDING_ADD_CARD[user_id]
    card = update.message.text.strip()
    if category not in CARDS:
        CARDS[category] = []
    CARDS[category].append(card)
    await update.message.reply_text(f"添加成功！{category} 已添加卡密，现在剩余 {len(CARDS[category])} 份")
    del PENDING_ADD_CARD[user_id]
    reply_markup = get_main_menu(user_id == ADMIN_ID)
    await update.message.reply_text("添加完成！请选择功能：", reply_markup=reply_markup)

async def handle_payment_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip().lower()
    user_id = update.effective_user.id
    if not text.startswith('已支付 '):
        return
    provided_order = text[4:].strip()
    if user_id not in PENDING_PAYMENTS:
        await update.message.reply_text("未找到待支付订单")
        return
    pending = PENDING_PAYMENTS[user_id]
    if provided_order != pending['order_id']:
        await update.message.reply_text("订单号不匹配")
        return
    category = pending['category']
    if category not in CARDS or not CARDS[category]:
        await update.message.reply_text(f"{category} 已售罄")
        del PENDING_PAYMENTS[user_id]
        return
    card = CARDS[category].pop(0)
    remain = len(CARDS[category])
    await update.message.reply_text(
        f"支付确认成功！\n卡密：{card}\n剩余 {remain} 份\n感谢支持～"
    )
    del PENDING_PAYMENTS[user_id]

# 保留命令方式添加卡密（备用）
async def add_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("无权限")
        return
    try:
        parts = update.message.text.split(maxsplit=2)
        if len(parts) < 3:
            raise ValueError
        _, category, card = parts
        card = card.strip()
        if category not in CARDS:
            CARDS[category] = []
        CARDS[category].append(card)
        await update.message.reply_text(f"添加成功！{category} 剩余 {len(CARDS[category])} 份")
    except:
        await update.message.reply_text("格式错误！示例：/add 1日体验 用户名:exp123 密码:abc456")

def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add", add_card))

    application.add_handler(CallbackQueryHandler(button_callback))

    # 消息处理：先支付确认，再添加卡密（避免冲突）
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_payment_confirm))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_card_message))

    # 针对 Python 3.14 + Render 环境的兼容写法
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,      # 启动时丢弃旧消息，避免堆积
            poll_interval=0.0,
            timeout=10,
            bootstrap_retries=-1,
            close_loop=False                # 防止关闭警告
        ))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Polling 异常: {e}")
    finally:
        # 清理
        loop.run_until_complete(application.stop())
        loop.close()

if __name__ == '__main__':
    main()



