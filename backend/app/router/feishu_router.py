import json
import time
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.service.lottery_service import perform_lottery
from app.config import settings

router = APIRouter(prefix="/feishu", tags=["feishu"])


def build_lottery_card(restaurant) -> dict:
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "template": "blue",
            "title": {"tag": "plain_text", "content": "🍜 今天吃啥？"}
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**🎉 中奖啦！**\n\n🍱 **{restaurant.name}**"
                }
            },
            {
                "tag": "hr"
            },
            {
                "tag": "div",
                "fields": [
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**地址**\n{restaurant.address if restaurant.address else '暂无'}"
                        }
                    },
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**评分**\n{restaurant.rating if restaurant.rating else '暂无'} ⭐"
                        }
                    }
                ]
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**简介**\n{restaurant.description if restaurant.description else '暂无描述'}"
                }
            },
            {
                "tag": "hr"
            },
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "🔄 再抽一次"},
                        "type": "primary",
                        "value": {"action": "redraw"}
                    }
                ]
            }
        ]
    }


def build_restaurant_list_card(restaurants) -> dict:
    elements = [
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**🍽️ 共收录 {len(restaurants)} 家餐厅**"
            }
        },
        {"tag": "hr"}
    ]
    
    for r in restaurants:
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**{r.name}**  ⭐ {r.rating if r.rating else '-'}\n📍 {r.address if r.address else '暂无地址'}"
            }
        })
        elements.append({"tag": "hr"})
    
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "template": "blue",
            "title": {"tag": "plain_text", "content": "🍜 餐厅列表"}
        },
        "elements": elements
    }


def build_help_card() -> dict:
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "template": "blue",
            "title": {"tag": "plain_text", "content": "🍜 今天吃啥 · 使用指南"}
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": (
                        "**🎲 随机抽取**\n"
                        "发送「吃啥」「抽签」「随便」「抽奖」「抽」\n\n"
                        "**📋 查看餐厅**\n"
                        "发送「列表」「餐厅」「菜单」\n\n"
                        "**❓ 获取帮助**\n"
                        "发送「帮助」「help」「?」\n\n"
                        "**💡 小提示**\n"
                        "选择困难？让机器人帮你决定今天吃什么！"
                    )
                }
            }
        ]
    }


@router.post("/webhook")
async def feishu_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        body = await request.json()
    except Exception as e:
        print(f"Webhook parse error: {e}")
        return {"challenge": ""}
    
    if "challenge" in body:
        return {"challenge": body["challenge"]}
    
    if "type" in body and body["type"] == "url_verification":
        return {"challenge": body.get("challenge", "")}
    
    event = body.get("event", {})
    if event.get("message_type") != "text":
        return {}
    
    text = event.get("text", "").strip()
    user_id = event.get("sender_id", {}).get("user_id", "")
    
    keywords_draw = ["吃啥", "抽签", "随便", "抽奖", "抽", "随机", "帮我选"]
    keywords_list = ["列表", "餐厅", "菜单", "有哪些"]
    keywords_help = ["帮助", "help", "?", "？", "怎么用"]
    
    from app.service.lottery_service import perform_lottery
    from app.service.restaurant_service import get_all_restaurants
    
    if any(k in text for k in keywords_help):
        card = build_help_card()
    elif any(k in text for k in keywords_list):
        restaurants = get_all_restaurants(db)
        if not restaurants:
            card = {
                "config": {"wide_screen_mode": True},
                "header": {"template": "red", "title": {"tag": "plain_text", "content": "⚠️ 暂无餐厅"}},
                "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": "暂无餐厅数据，请先添加餐厅～"}}]
            }
        else:
            card = build_restaurant_list_card(restaurants[:20])
    elif any(k in text for k in keywords_draw):
        result = perform_lottery(db, winner_user_id=user_id)
        if result is None:
            card = {
                "config": {"wide_screen_mode": True},
                "header": {"template": "red", "title": {"tag": "plain_text", "content": "⚠️ 暂无餐厅"}},
                "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": "暂无餐厅可抽，先去添加几家吧～"}}]
            }
        else:
            card = build_lottery_card(result.restaurant)
    else:
        card = build_help_card()
    
    return {
        "msg_type": "interactive",
        "card": card
    }


@router.post("/events")
async def feishu_events(request: Request, db: Session = Depends(get_db)):
    return await feishu_webhook(request, db)
