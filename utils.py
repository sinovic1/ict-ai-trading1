from telegram import Update

AUTHORIZED_USER_ID = 7469299312

def is_authorized(update: Update) -> bool:
    return update.effective_user and update.effective_user.id == AUTHORIZED_USER_ID

def format_signal(signal: dict) -> str:
    return (
        f"📈 *{signal['pair']}* Signal\n"
        f"• Entry: `{signal['entry']}`\n"
        f"• TP1: `{signal['tp1']}`\n"
        f"• TP2: `{signal['tp2']}`\n"
        f"• TP3: `{signal['tp3']}`\n"
        f"• SL: `{signal['sl']}`\n"
        f"• Strategy: {signal['strategy']}"
    )
