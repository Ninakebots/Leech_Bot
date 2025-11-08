from logging import FileHandler, StreamHandler, INFO, basicConfig, error as log_error, info as log_info
from os import path as ospath, environ, remove
from subprocess import run as srun, call as scall
from pkg_resources import working_set
from requests import get as rget
from dotenv import load_dotenv, dotenv_values
from pymongo import MongoClient

if ospath.exists('log.txt'):
    with open('log.txt', 'r+') as f:
        f.truncate(0)

if ospath.exists('rlog.txt'):
    remove('rlog.txt')

basicConfig(format="[%(asctime)s] [%(levelname)s] - %(message)s",
            datefmt="%d-%b-%y %I:%M:%S %p",
            handlers=[FileHandler('log.txt'), StreamHandler()],
            level=INFO)

load_dotenv('config.env', override=True)

try:
    if bool(environ.get('_____REMOVE_THIS_LINE_____')):
        log_error('The README.md file there to be read! Exiting now!')
        exit()
except:
    pass

BOT_TOKEN = environ.get('BOT_TOKEN', '')
if len(BOT_TOKEN) == 0:
    log_error("BOT_TOKEN variable is missing! Exiting now")
    exit(1)

bot_id = BOT_TOKEN.split(':', 1)[0]

DATABASE_URL = environ.get('DATABASE_URL', '')
if len(DATABASE_URL) == 0:
    DATABASE_URL = None

if DATABASE_URL is not None:
    conn = MongoClient(DATABASE_URL)
    db = conn.kpsmlx
    old_config = db.settings.deployConfig.find_one({'_id': bot_id})
    config_dict = db.settings.config.find_one({'_id': bot_id})
    if old_config is not None:
        del old_config['_id']
    if (old_config is not None and old_config == dict(dotenv_values('config.env')) or old_config is None) \
            and config_dict is not None:
        environ['UPSTREAM_REPO'] = config_dict['UPSTREAM_REPO']
        environ['UPSTREAM_BRANCH'] = config_dict['UPSTREAM_BRANCH']
        environ['UPGRADE_PACKAGES'] = config_dict.get('UPDATE_PACKAGES', 'False')
    conn.close()

UPGRADE_PACKAGES = environ.get('UPGRADE_PACKAGES', 'False') 
if UPGRADE_PACKAGES.lower() == 'true':
    packages = [dist.project_name for dist in working_set]
    scall("uv pip install --system " + ' '.join(packages), shell=True)

UPSTREAM_REPO = environ.get('UPSTREAM_REPO', '')
if len(UPSTREAM_REPO) == 0:
    UPSTREAM_REPO = "https://github.com/Tamilupdates/KPSML-X"

UPSTREAM_BRANCH = environ.get('UPSTREAM_BRANCH', '')
if len(UPSTREAM_BRANCH) == 0:
    UPSTREAM_BRANCH = 'hk_kpsmlx'

def update_bot():
    """Function to update the bot from upstream repository"""
    try:
        log_info('Starting update process...')
        
        if ospath.exists('.git'):
            srun(["rm", "-rf", ".git"])
            
        update_process = srun([f"git init -q \
                              && git config --global user.email doc.adhikari@gmail.com \
                              && git config --global user.name weebzone \
                              && git add . \
                              && git commit -sm update -q \
                              && git remote add origin {UPSTREAM_REPO} \
                              && git fetch origin -q \
                              && git reset --hard origin/{UPSTREAM_BRANCH} -q"], shell=True)
        
        repo = UPSTREAM_REPO.split('/')
        UPSTREAM_REPO_FULL = f"https://github.com/{repo[-2]}/{repo[-1]}"
        
        if update_process.returncode == 0:
            log_info('Successfully updated with latest commits!')
            return True, "Successfully updated with latest commits!"
        else:
            log_error('Update failed!')
            return False, "Update failed! Please check logs for details."
            
    except Exception as e:
        log_error(f'Error during update: {str(e)}')
        return False, f"Error during update: {str(e)}"

# Auto-update on startup
if UPSTREAM_REPO is not None:
    success, message = update_bot()
    log_info(f'UPSTREAM_REPO: {UPSTREAM_REPO} | UPSTREAM_BRANCH: {UPSTREAM_BRANCH}')

# /update command handler function (to be integrated with your bot)
async def update_command(update, context):
    """Handle the /update command"""
    try:
        # Check if user is authorized to update
        user_id = update.message.from_user.id
        # Add your authorization logic here (e.g., check if user is owner/admin)
        
        # Send initial message
        message = await update.message.reply_text("🔄 Updating bot from upstream repository...")
        
        # Perform update
        success, update_message = update_bot()
        
        if success:
            response_text = f"✅ {update_message}\n\nBot will now restart to apply changes."
            await message.edit_text(response_text)
            
            # Restart the bot
            import sys
            import os
            os.execl(sys.executable, sys.executable, *sys.argv)
        else:
            response_text = f"❌ {update_message}\n\nPlease check logs for more details."
            await message.edit_text(response_text)
            
    except Exception as e:
        error_msg = f"Error executing update command: {str(e)}"
        log_error(error_msg)
        await update.message.reply_text(f"❌ {error_msg}")

# Alternative /update command with more detailed output
async def detailed_update_command(update, context):
    """Handle the /update command with detailed progress"""
    try:
        user_id = update.message.from_user.id
        # Add authorization check here
        
        progress_message = await update.message.reply_text(
            "🔄 Starting update process...\n"
            "▰▱▱▱▱▱▱▱▱ 10%"
        )
        
        # Step 1: Remove existing git
        await progress_message.edit_text(
            "🔄 Removing existing git repository...\n"
            "▰▰▱▱▱▱▱▱▱ 20%"
        )
        
        if ospath.exists('.git'):
            srun(["rm", "-rf", ".git"])
        
        # Step 2: Initialize git
        await progress_message.edit_text(
            "🔄 Initializing git...\n"
            "▰▰▰▱▱▱▱▱▱ 30%"
        )
        
        # Step 3: Perform the actual update
        await progress_message.edit_text(
            "🔄 Fetching latest changes...\n"
            "▰▰▰▰▰▱▱▱▱ 50%"
        )
        
        success, update_message = update_bot()
        
        if success:
            await progress_message.edit_text(
                "✅ Successfully updated!\n"
                "▰▰▰▰▰▰▰▰▰▰ 100%\n\n"
                "Restarting bot to apply changes..."
            )
            
            # Restart after a short delay
            import asyncio
            await asyncio.sleep(2)
            import sys
            import os
            os.execl(sys.executable, sys.executable, *sys.argv)
        else:
            await progress_message.edit_text(
                f"❌ Update failed!\n"
                f"Error: {update_message}\n\n"
                "Please check logs for more details."
            )
            
    except Exception as e:
        log_error(f"Error in detailed update: {str(e)}")
        await update.message.reply_text(f"❌ Update failed: {str(e)}")

# Function to register the update command with your bot
def register_update_handlers(application):
    """Register update command handlers with the bot"""
    from telegram.ext import CommandHandler
    
    # Register the basic update command
    application.add_handler(CommandHandler("update", update_command))
    
    # Optional: Register detailed update command with different name
    application.add_handler(CommandHandler("update_detailed", detailed_update_command))
