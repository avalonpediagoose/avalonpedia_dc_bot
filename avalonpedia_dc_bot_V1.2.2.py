
#阿瓦隆dc bot v1.2
#新增修改bot貼文
#新增掛掉的時候關掉driver，!quit
###############################
#阿瓦隆dc bot v1.1
#新增bot自動論壇貼文
#新增tag

import discord
from discord.ext import commands
from discord import Embed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import asyncio
import re
import os
from datetime import datetime

TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="+",intents=intents,help_command=None)
user_sessions = {}  # user_id: driver
# 用來記錄日期與場次次數（記憶體內部保存）
last_date = None
event_counts = {}

######################################################################################################
#加入房間
def join_room(room_input):
    try:   
        #開始跑網頁
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1200,1080')
        driver=webdriver.Chrome(options=options)
        ult="https://avalon.signage-cloud.org/" #可改
        driver.get(ult)
        username=driver.find_element(By.CLASS_NAME,"form-control")
        username.send_keys("派票紀錄員") #輸入玩家名字
        btn=driver.find_element(By.CLASS_NAME,"btn-block") #定義button
        btn.click() #點擊進入頁面
        time.sleep(2)

        # 抓取所有房間項目 <li class="list-group-item">
        rooms = driver.find_elements(By.CSS_SELECTOR, 'li.list-group-item')
        # 指定你要找的房間號碼
        target_room_id = f"#room_{room_input}"
        found = False
        for room in rooms:
            try:
                # 找到房號
                badge = room.find_element(By.XPATH, './/span[contains(@class, "badge") and contains(text(), "#room_")]')
                room_id = badge.text.strip()

                if room_id == target_room_id:
                    #print(f"✅ 找到目標房間 {room_id}")
                    # 在這個房間區塊中找「觀眾席」按鈕
                    btn = room.find_element(By.CLASS_NAME, "btn-info")
                    btn.click()
                    #print("🎥 點擊觀眾席按鈕成功！")
                    found = True
                    return True, driver,f"✅ 成功進入房間 {room_id}"
            except Exception as e:
                continue
        if not found:
            driver.quit()
            return False, None, f"❌ 找不到房間 #room_{room_input}，請重新輸入!room 房號"
    except Exception as e:
        return False, f"⚠️ 發生錯誤：{e}"

########################################################################################################################################
#記錄派票
def record_after_game(driver,input_value):
    try:
        lake_lady=[i for i in input_value]
        kill = lake_lady[-1]
        r=int(lake_lady[0])
        i=0
        a=0
        ticket=[]
        white=[]
        black=[]
        cup=[]
        ticket_record=[]
        btn = driver.find_element(By.CSS_SELECTOR, 'button[data-toggle="modal"].btn.btn-primary')
        btn.click()
        time.sleep(2)
        btn = driver.find_element(By.XPATH, '//a[text()="第二局"]')
        i=0
        #定義局數、黑白球、好壞杯
        for round_number in range(1,r+1):
            time.sleep(1)
            round_id = f"round_{round_number}"
            round=driver.find_element(By.ID,round_id)#定義第幾局
            round_tds=round.find_elements(By.TAG_NAME,"td")#派票黑白球
            round_cups=round.find_elements(By.CLASS_NAME,"col-sm-2")#好壞杯
            #紀錄派票黑白球
            for round_td in round_tds:
                if "正常黑"in round_td.text or"場外白"in round_td.text or"場內黑"in round_td.text or"正常白"in round_td.text or"抗議黑"in round_td.text:
                    i+=1
                    if i==10:
                        i=0
                        a=99
                    if "場外白"in round_td.text:
                        white.append(i)
                    if "抗議黑"in round_td.text or"場內黑"in round_td.text:
                        black.append(i)
                    if "image/mission.jpg" in round_td.get_attribute("innerHTML"):
                        ticket.append(i)
                if a==99:
                    all_white=''.join(map(str,white))
                    all_black=''.join(map(str,black))
                    all_ticket=''.join(map(str,ticket))
                    if white or black:
                        if white and black:
                            ticket_record.append(all_ticket+' '+all_white+'+'+all_black+'-')
                        elif white:
                            ticket_record.append(all_ticket+' '+all_white+'+')
                        elif black:
                            ticket_record.append(all_ticket+' '+all_black+'-')
                    else:
                        ticket_record.append(all_ticket)
                    i=0
                    a=0
                    ticket=[]
                    white=[]
                    black=[]
            #紀錄好壞杯
            for round_cup in round_cups:
                if "image/good_cup.jpg" in round_cup.get_attribute("innerHTML"):
                    cup.append("O")
                elif "image/bad_cup.jpg" in round_cup.get_attribute("innerHTML"):
                    cup.append("X")
            all_cup=''.join(map(str,cup))
            ticket_record.append(all_cup)
            cup=[]
            if round_number==r:
                break
            if round_number==1:
                btn.click()       
                btn = driver.find_element(By.XPATH, '//a[text()="第三局"]')
            if round_number==2:
                ticket_record.append(f"0>{lake_lady[1]} {lake_lady[2]}")
                btn.click()
                btn = driver.find_element(By.XPATH, '//a[text()="第四局"]')
            if round_number==3:
                ticket_record.append(f"{lake_lady[1]}>{lake_lady[3]} {lake_lady[4]}")
                btn.click()
                btn = driver.find_element(By.XPATH, '//a[text()="第五局"]')
            if round_number==4:
                ticket_record.append(f"{lake_lady[3]}>{lake_lady[5]} {lake_lady[6]}")
                btn.click()



        #紀錄玩家名稱
        time.sleep(1)
        players = [player.text for player in driver.find_elements(By.CSS_SELECTOR, "[align=center]")]
        # 如果抓不到10位，補空
        while len(players) < 10:
            players.append("")
        play_order = [0, 1, 2, 3, 4, 5, 8, 9, 7, 6]
        player_list = ""
        for i, idx in enumerate(play_order):
            number = (i + 1) % 10  # 讓第10個變成 0
            player_list += f"{number}.{players[idx]}\n"

        #紀錄特殊角色位置
        role_map = {
            "刺客": 0,
            "莫甘娜": 1,
            "莫德雷德": 2,
            "奧伯倫": 3,
            "派西維爾": 4,
            "梅林": 5
        }
        player_role = [0] * 6
        roles = driver.find_elements(By.CLASS_NAME, "col-sm-12")
        for role_elem in roles:
            html = role_elem.get_attribute("innerHTML")
            for name, role_idx in role_map.items():
                if f"image/Q_{name}.jpg" in html:
                    match = re.search(r'image/p(\d+)\.png', html)
                    if match:
                        player_number = (int(match.group(1)) + 1) % 10  # ✅ 將 10 顯示為 0
                        player_role[role_idx] = player_number
        # 只取順序為：刺客、莫甘娜、莫德雷德、派西維爾、梅林
        player_role = "".join(str(player_role[i]) for i in [0, 1, 2, 3, 4, 5])

        driver.quit()

        if kill.lower() != "x":
        
            if kill == player_role[5]:
                tag = "三藍被刀"
            else:
                tag = "三藍躲刺"
        else:
            tag = "三紅"
        
        return True,player_role,player_list,"\n".join(ticket_record),kill,tag
    
    except Exception as e:
        return False, f"⚠️ 發生錯誤：{e}"

####################################################################
#Bot回應
@bot.event
async def on_ready():
    print(f"✅ Bot 已登入：{bot.user}")


#加入房間
@bot.command()
async def room(ctx, room_number: str):
    # 限制只能在 #活動 頻道使用(可以自行變更)
    if ctx.channel.name != "紀錄爬蟲用":#看要加在哪一個頻道
        await ctx.send("❌ 這個指令只能在 #紀錄爬蟲用 頻道使用！")
        return

    await ctx.send(f"🔍 嘗試進入房間 #room_{room_number} 中...")
    success, driver, msg = await asyncio.to_thread(join_room, room_number)
    await ctx.send(msg)

    if success:
        user_sessions[ctx.author.id] = driver
        await ctx.send("💡 如果要記錄派票請打 `+record`")
        await ctx.send("🎙️ 如果要加入語音請打 `+voice 語音房名`")   
    else:
        return


#記錄派票(牌局結束後)
@bot.command()
async def record(ctx):
    driver = user_sessions.get(ctx.author.id)
    if not driver:
        await ctx.send("❌ 請先使用 `+room 房號` 指令進入房間！")
        return
    await ctx.send("請輸入局數、湖中、刺殺誰(沒有刺殺請打X)：")
    await ctx.send("範例1 ：34o5-->3局，0湖4好，三藍刺殺5")
    await ctx.send("範例2 ：54o8o1xx-->5局，0湖4好、4湖8好、8湖1壞，三紅沒有刺殺")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        user_input = await bot.wait_for("message", timeout=600.0, check=check)  #timeout秒數可以更改
        await ctx.send(f"📥 已收到，開始記錄派票...")

        #訂標題(0726一般場1)
        global last_date, event_counts
        today = datetime.now().strftime("%m%d")
        event_key = "一般場"
        if last_date != today:
            event_counts = {}
            last_date = today
        event_counts[event_key] = event_counts.get(event_key, 0) + 1
        event_name = f"{today}{event_key}{event_counts[event_key]}"
        await ctx.send(f"📌 {event_name}")

        # ✅ 加入這段：截圖
        screenshot_path = f"{event_name}.png"
        driver.save_screenshot(screenshot_path)
        file = discord.File(screenshot_path)

        # 執行你的處理邏輯
        success, msg_players_role, msg_players_list, msg_players_ticket, msg_kill ,msg_tag = await asyncio.to_thread(
            record_after_game, driver, user_input.content
        )

        await ctx.send(msg_players_ticket)
        await ctx.send(f"刺客刺殺：{msg_kill}")
        await ctx.send(msg_players_role)
        await ctx.send(msg_players_list)
        with open(screenshot_path, "rb") as f:
            file = discord.File(f)
            await ctx.send(file=file)
        await ctx.send(f"標籤：⚔️線瓦 {msg_tag}")

        # ✅ 發到論壇頻道
        forum_channel = bot.get_channel(1399732441115004978)  #更改論壇ID
        if isinstance(forum_channel, discord.ForumChannel):
            # 正確地找出 tag 物件
            tag1 = discord.utils.get(forum_channel.available_tags, name = "線瓦")
            tag2 = discord.utils.get(forum_channel.available_tags, name = msg_tag)
            if tag1 is None:
                await ctx.send("⚠️ 找不到 tag『線瓦』，請先到論壇頻道手動新增此標籤。")
                return

            message = await forum_channel.create_thread(
                name=event_name,
                content=(
                    f"{msg_players_ticket}\n"
                    f"刺客刺殺：{msg_kill}\n"
                    f"{msg_players_role}\n"
                    f"{msg_players_list}"
                ),
                applied_tags=[tag1, tag2]
            )
            with open(screenshot_path, "rb") as f:
                file = discord.File(f)
                await message.thread.send(file=file)
        else:
            await ctx.send("⚠️ 找不到論壇頻道或類型錯誤，請確認頻道 ID 正確。")


        # 清理
        driver.quit()
        del user_sessions[ctx.author.id]
        os.remove(screenshot_path)
    except asyncio.TimeoutError:
        await ctx.send("⏰ 超過 600 秒未輸入，已取消。")
        driver.quit()
        del user_sessions[ctx.author.id]

#功能介紹
@bot.command()
async def help(ctx):
    embed = Embed(
        title="📖 Avalon Bot 使用說明",
        description="這是用來輔助 [阿瓦隆練習台1.42版](https://avalon.signage-cloud.org/) 的工具，以下是可用指令：",
        color=0x3498db  # 藍色
    )

    embed.add_field(
        name="🎯 **進入房間**",
        value="🔹 指令：`+room 房號`\n🔹 範例：`+room 50`\n🔹 功能：進入指定房間的觀眾席。",
        inline=False
    )

    embed.add_field(
        name="📝 **記錄派票紀錄**",
        value="🔹 指令：`+record`\n🔹 功能：進房成功後，記錄牌局結束後的派票資訊。\n🔹 範例1 ：34o5-->3局，0湖4好，三藍刺殺5\n🔹 範例2 ：54o8o1xx-->5局，0湖4好、4湖8好、8湖1壞，三紅沒有刺殺",
        inline=False
    )

    embed.add_field(
        name="📝 **貼文內容修改**",
        value="🔹 指令：`+修改 貼文標題`\n🔹 功能：可修改貼文錯誤的內容，請修改後將所以文字貼上。\n🔹 範例：`+修改 0731一般場1`",
        inline=False
    )

    embed.add_field(
        name="📝 **貼文內容修改**",
        value="🔹 指令：`+quit`\n🔹 功能：掛掉的時候，關掉driver。",
        inline=False
    )

    embed.set_footer(text="開發者：TonioCatzz")
    await ctx.send(embed=embed)


#修改內文
@bot.command()
async def 修改(ctx, *, title: str):
    """根據論壇標題修改主題內容"""
    forum_channel = bot.get_channel(1399732441115004978)  # 替換成你的論壇頻道 ID

    if not isinstance(forum_channel, discord.ForumChannel):
        await ctx.send("❌ 找不到正確的論壇頻道，請確認 ID 是否正確。")
        return

    # 嘗試從主題中找出匹配標題的 Thread
    target_thread = None
    for thread in forum_channel.threads:
        if thread.name == title:
            target_thread = thread
            break

    if not target_thread:
        await ctx.send(f"❌ 沒有找到標題為「{title}」的主題。")
        return

    # 要求使用者輸入新的內容
    await ctx.send(f"請輸入「{title}」的新內文：")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        new_content = await bot.wait_for("message", timeout=300.0, check=check)

        # 取得該主題的起始訊息
        starter_message = await target_thread.fetch_message(target_thread.id)
        await starter_message.edit(content=new_content.content)

        await ctx.send(f"✅ 已成功更新「{title}」的內容。")

    except discord.NotFound:
        await ctx.send("❌ 找不到主題開頭訊息，可能已被刪除。")
    except asyncio.TimeoutError:
        await ctx.send("⏰ 超時，請重新輸入指令。")
    except Exception as e:
        await ctx.send(f"⚠️ 發生錯誤：{str(e)}")

@bot.command()
async def quit(ctx, member: discord.Member = None):
    """
    結束指定成員的 driver（限管理員），如果沒指定則結束自己的。
    使用方式：
    +quit              --> 結束自己的 driver
    +quit @某人         --> 管理員可結束別人的 driver
    """
    # 預設為自己
    target_member = member or ctx.author

    # 如果目標不是自己，檢查是否有管理權限
    if target_member != ctx.author and not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ 你沒有權限關閉其他人的 driver。")
        return

    driver = user_sessions.get(target_member.id)
    if not driver:
        if target_member == ctx.author:
            await ctx.send("⚠️ 你目前沒有啟動中的 driver。")
        else:
            await ctx.send(f"⚠️ {target_member.display_name} 沒有啟動中的 driver。")
        return

    try:
        driver.quit()
        del user_sessions[target_member.id]
        if target_member == ctx.author:
            await ctx.send("✅ 你的 driver 已成功結束。")
        else:
            await ctx.send(f"✅ 已成功結束 {target_member.display_name} 的 driver。")
    except Exception as e:
        await ctx.send(f"⚠️ 關閉 driver 時發生錯誤：{str(e)}")

bot.run(TOKEN)


