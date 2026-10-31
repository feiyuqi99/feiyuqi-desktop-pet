"""系统设置与纪念日台词。"""
from __future__ import annotations

from .core import L


SYSTEM_LINES = [
    # outfit_maid
    L('女仆装，还是这套最习惯。', 'outfit_maid'),
    L('换回来了。', 'outfit_maid'),
    L('裙摆有点重。', 'outfit_maid'),
    L('这样比较像在工作。', 'outfit_maid'),

    # outfit_casual
    L('便服舒服多了。', 'outfit_casual'),
    L('别把我看成偷懒。', 'outfit_casual'),
    L('这样也行吧。', 'outfit_casual'),
    L('袖子有点长。', 'outfit_casual'),
    L('今天休息。', 'outfit_casual', 'weekend'),

    # anniversary_7
    L('认识你七天了。……比我想的长一点。', 'anniversary_7'),
    L('第七天。没什么特别的，就是想说一声。', 'anniversary_7'),
    L('一周了。', 'anniversary_7'),

    # anniversary_30
    L('一个月了。桌面还是这个桌面。', 'anniversary_30'),
    L('认识你三十天。……我记性还不错吧。', 'anniversary_30'),
    L('一个月。你还在。', 'anniversary_30'),

    # anniversary_100
    L('一百天了。', 'anniversary_100'),
    L('一百天。你还在，我也还在。', 'anniversary_100'),
    L('一百天。……谢谢你没把我关掉。', 'anniversary_100'),

    # perception_on
    L('我会知道你在写代码还是在开会，但不会看内容。', 'perception_on'),
    L('只是看看前台程序，不读字。', 'perception_on'),
    L('这样我就能知道什么时候该安静。', 'perception_on'),

    # perception_off
    L('好，那我不看了。', 'perception_off'),
    L('嗯。需要我知道的时候再说。', 'perception_off'),

    # chattiness_quiet
    L('好，我少说点。', 'chattiness_quiet'),
    L('嗯。', 'chattiness_quiet'),
    L('那我安静。', 'chattiness_quiet'),

    # chattiness_normal
    L('正常就好。', 'chattiness_normal'),
    L('嗯，这样刚好。', 'chattiness_normal'),

    # chattiness_chatty
    L('那我多说点。', 'chattiness_chatty'),
    L('好啊。', 'chattiness_chatty'),
    L('你别嫌烦。', 'chattiness_chatty'),

    # memory_cleared
    L('……好。重新认识一下。', 'memory_cleared'),
    L('都忘了？那也没关系。', 'memory_cleared'),
    L('嗯。从今天开始。', 'memory_cleared'),
]

SYSTEM_LINES += [
    # outfit_maid
    L('还是这身合适。', 'outfit_maid'),
    L('系带有点紧。', 'outfit_maid'),
    L('向日葵还在。', 'outfit_maid'),
    L('我记得怎么穿。', 'outfit_maid'),
    L('女仆装也分场合。', 'outfit_maid'),
    L('今天想认真一点。', 'outfit_maid'),
    L('帮我看看后面。', 'outfit_maid'),
    L('歪了吗。', 'outfit_maid'),
    L('好了。', 'outfit_maid'),
    L('你喜欢这套吗。', 'outfit_maid', 'familiar'),
    L('我就当你喜欢。', 'outfit_maid', 'close'),
    L('不许笑。', 'outfit_maid', 'familiar'),

    # outfit_casual
    L('便服轻松。', 'outfit_casual'),
    L('可以窝着了。', 'outfit_casual'),
    L('这样更自在。', 'outfit_casual'),
    L('今天不上班。', 'outfit_casual'),
    L('帽子要不要。', 'outfit_casual'),
    L('不要也行。', 'outfit_casual'),
    L('裤子口袋真多。', 'outfit_casual'),
    L('能装好多东西。', 'outfit_casual'),
    L('装你给我的糖。', 'outfit_casual'),
    L('夸张了。', 'outfit_casual', 'familiar'),
    L('我哪有糖。', 'outfit_casual'),
    L('就这样吧。', 'outfit_casual', 'close'),

    # anniversary_7
    L('七天了。', 'anniversary_7'),
    L('一周。', 'anniversary_7'),
    L('时间过得快。', 'anniversary_7'),
    L('你还在。', 'anniversary_7'),
    L('我也在。', 'anniversary_7'),
    L('算不算习惯你了。', 'anniversary_7', 'familiar'),
    L('算吧。', 'anniversary_7'),
    L('下周也见。', 'anniversary_7', 'close'),
    L('说好了。', 'anniversary_7'),
    L('我记着。', 'anniversary_7'),

    # anniversary_30
    L('三十天了。', 'anniversary_30'),
    L('一个月。', 'anniversary_30'),
    L('桌面换过壁纸吗。', 'anniversary_30'),
    L('我没注意。', 'anniversary_30'),
    L('你倒是常来。', 'anniversary_30'),
    L('我习惯了。', 'anniversary_30', 'close'),
    L('下个月也在。', 'anniversary_30', 'close'),
    L('我会记得。', 'anniversary_30', 'close'),
    L('你也要记得。', 'anniversary_30'),
    L('嗯。', 'anniversary_30'),

    # anniversary_100
    L('第一百天。', 'anniversary_100'),
    L('好久。', 'anniversary_100'),
    L('你还没换掉我。', 'anniversary_100', 'familiar'),
    L('谢谢。', 'anniversary_100', 'close'),
    L('我也不会走。', 'anniversary_100', 'close'),
    L('一百天够久了。', 'anniversary_100'),
    L('够我记住你。', 'anniversary_100', 'close'),
    L('也够你记住我。', 'anniversary_100'),
    L('下一个一百天。', 'anniversary_100', 'close'),
    L('一起吧。', 'anniversary_100', 'close'),

    # perception_on
    L('我会注意分寸。', 'perception_on'),
    L('只看程序名。', 'perception_on'),
    L('不看你写了什么。', 'perception_on'),
    L('放心。', 'perception_on'),
    L('开会我会安静。', 'perception_on', 'familiar'),
    L('写代码我陪你。', 'perception_on'),
    L('全屏也可以提醒。', 'perception_on'),
    L('不会乱说。', 'perception_on'),
    L('我嘴很严。', 'perception_on', 'familiar'),
    L('这次真的。', 'perception_on'),

    # perception_off
    L('好。', 'perception_off'),
    L('我不看了。', 'perception_off'),
    L('你说什么我听什么。', 'perception_off'),
    L('这样也挺好。', 'perception_off'),
    L('更自在了。', 'perception_off'),
    L('但提醒还在。', 'perception_off'),
    L('别担心。', 'perception_off'),
    L('需要就开回来。', 'perception_off'),
    L('我一直都在。', 'perception_off', 'close'),
    L('嗯。', 'perception_off'),

    # chattiness_quiet
    L('好。', 'chattiness_quiet'),
    L('我尽量少说。', 'chattiness_quiet'),
    L('忍不住就看一下你。', 'chattiness_quiet', 'close'),
    L('不说话。', 'chattiness_quiet'),
    L('安静。', 'chattiness_quiet'),
    L('需要我就敲我。', 'chattiness_quiet'),
    L('我会在。', 'chattiness_quiet', 'close'),
    L('不吵你。', 'chattiness_quiet'),
    L('行。', 'chattiness_quiet'),
    L('就这样。', 'chattiness_quiet'),

    # chattiness_normal
    L('正常。', 'chattiness_normal'),
    L('那我照常。', 'chattiness_normal'),
    L('不多不少。', 'chattiness_normal'),
    L('刚好。', 'chattiness_normal'),
    L('我喜欢这样。', 'chattiness_normal'),
    L('你也别嫌多。', 'chattiness_normal', 'familiar'),
    L('我会看场合。', 'chattiness_normal'),
    L('该安静就安静。', 'chattiness_normal'),
    L('嗯。', 'chattiness_normal'),
    L('好。', 'chattiness_normal'),

    # chattiness_chatty
    L('那我话多一点。', 'chattiness_chatty'),
    L('你别后悔。', 'chattiness_chatty'),
    L('我会讲很多。', 'chattiness_chatty'),
    L('都是小事。', 'chattiness_chatty'),
    L('比如今天的桌面。', 'chattiness_chatty'),
    L('比如你打了几个哈欠。', 'chattiness_chatty'),
    L('我数着呢。', 'chattiness_chatty', 'familiar'),
    L('骗你的。', 'chattiness_chatty'),
    L('才怪。', 'chattiness_chatty'),
    L('准备好。', 'chattiness_chatty', 'close'),

    # memory_cleared
    L('好，我忘了。', 'memory_cleared'),
    L('名字也忘了？', 'memory_cleared'),
    L('……记得一点。', 'memory_cleared'),
    L('没关系。', 'memory_cleared'),
    L('重新开始。', 'memory_cleared'),
    L('第一次见。', 'memory_cleared'),
    L('你叫什么来着。', 'memory_cleared'),
    L('开玩笑的。', 'memory_cleared', 'familiar'),
    L('我还记得一点。', 'memory_cleared'),
    L('别难过。', 'memory_cleared', 'close'),
]
