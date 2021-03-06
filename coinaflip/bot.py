import random
import uuid

seen = {}
bot = None


async def on_update(update):
    query = update.inline_query.query
    if not isinstance(query, str):
        if update.message.chat.type == 'private':
            state = seen.get(update.message.chat.id)
            if not state:
                seen[update.message.chat.id] = 1
                await bot.sendMessage(
                    chat_id=update.message.chat.id,
                    text='I only work inline silly. Anyway, @LonamiWebs made '
                         'me, and Richard hosts the server so thank him ❤️'
                )
            elif state == 1:
                seen[update.message.chat.id] = 2
                await bot.sendMessage(
                    chat_id=update.message.chat.id,
                    text="Hey, look, I don't have anything new to say."
                )
        return

    flip = random.choices(('Heads!', 'Tails!', '…fell on its side'), (0.495, 0.495, 0.01))[0]
    await bot.answerInlineQuery(
        inline_query_id=update.inline_query.id,
        results=[dict(
            type='article',
            id=str(uuid.uuid4()),
            title='Flip a coin!',
            input_message_content=dict(message_text=flip)
        )],
        cache_time=0
    )
