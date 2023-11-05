import os
from telethon.sync import TelegramClient, errors
import asyncio
from telethon.sessions import StringSession
from creds import api_id, api_hash, session_string, source_channel_id, destination_channel_id



# Define the file to store the last offset and the set to store forwarded post IDs
offset_file = 'offset.txt'
forwarded_post_ids = set()

async def remove_forward_tag(post_text):
    # Check if the post contains a "forwarded from" tag
    if "forwarded from" in post_text:
        # Split the text at the "forwarded from" tag
        post_text = post_text.split("forwarded from")[0].strip()
    return post_text

async def forward_posts():
    async with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
        # Check if the offset file exists
        if os.path.exists(offset_file):
            with open(offset_file, 'r') as f:
                offset = int(f.read())
        else:
            offset = 0  # Start forwarding from the first post

        if offset == 0:
            print("Starting from the first post.")
            # Reset the offset to ensure it starts from the first post
            with open(offset_file, 'w') as f:
                f.write(str(offset))

        while True:
            try:
                source_channel = int(source_channel_id)
                destination_channel = int(destination_channel_id)

                posts = await client.get_messages(source_channel, limit=1, offset_id=offset, reverse=True)

                if posts is None or not posts:
                    print("No posts available to forward.")
                    break

                post = posts[0]
                offset = post.id  # Update the offset to the last forwarded post

                if post.id not in forwarded_post_ids:
                    post_text = post.text
                    post_text = await remove_forward_tag(post_text)
                    
                    if post.media:
                        await client.send_file(destination_channel, post.media, caption=post_text)
                        print(f"Forwarded post {post.id} with media and without forward tag.")
                    elif post.text:
                        await client.send_message(destination_channel, post_text)
                        print(f"Forwarded post {post.id} without media and without forward tag.")
                    
                    # Add the forwarded post ID to the set
                    forwarded_post_ids.add(post.id)

                    # Update the offset in the file
                    with open(offset_file, 'w') as f:
                        f.write(str(post.id + 1))

                await asyncio.sleep(7200)  # 1-second delay

            except errors.FloodWaitError as e:
                print(f"Flood wait error. Sleeping for {e.seconds} seconds.")
                await asyncio.sleep(e.seconds)
            except errors.RPCError as e:
                print(f"RPC error: {e}")
                break  # Stop the code on RPC error
            except Exception as e:
                print(f"An error occurred: {e}")
                # Clear the offset file
                with open(offset_file, 'w') as f:
                    f.write('0')
             # Stop the code on any other error

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    while True:
        try:
            loop.run_until_complete(forward_posts())
        except KeyboardInterrupt:
            print("Bot stopped by the user.")
            break
