"""计时、关怀与音乐台词。"""
from __future__ import annotations

from .core import L


COMPANION_LINES = [
    # hourly
    L('{time} 了。喝口水吧。', 'hourly'),
    L('整点了。起来动一下。', 'hourly'),
    L('{time}。时间过得挺快。', 'hourly'),
    L('又过去一小时。', 'hourly'),
    L('报时：{time}。……我是不是很无聊。', 'hourly'),
    L('都 {time} 了。', 'hourly', 'late_hours'),
    L('{time} 了，代码不会跑，人会累。', 'hourly', 'coding'),
    L('{time}。还顺利吗。', 'hourly', 'familiar'),

    # sit
    L('坐了很久了，站起来伸个懒腰吧。', 'sit'),
    L('腰会疼的。', 'sit'),
    L('去接杯水？', 'sit'),
    L('我陪你站一会儿。', 'sit'),
    L('站起来，走两步。', 'sit'),
    L('别装没看见。', 'sit'),
    L('久坐提醒。……这次是真的很久。', 'sit'),

    # pomo_start
    L('25 分钟。我陪你。', 'pomo_start'),
    L('开始吧。我不吵你。', 'pomo_start'),
    L('专心。', 'pomo_start'),
    L('好，计时开始了。', 'pomo_start'),
    L('这 25 分钟归你。', 'pomo_start'),

    # pomo_break
    L('先休息五分钟。', 'pomo_break'),
    L('站起来，看看远处。', 'pomo_break'),
    L('喝水。', 'pomo_break'),
    L('别急着继续。', 'pomo_break'),
    L('休息也是正事。', 'pomo_break'),

    # pomo_end
    L('时间到。先站起来，别急着继续。', 'pomo_end'),
    L('25 分钟到了。', 'pomo_end'),
    L('做得不错。休息一下。', 'pomo_end'),
    L('停一下。眼睛也需要。', 'pomo_end'),
    L('结束了。你比刚才更专注了。', 'pomo_end'),

    # pomo_break_end
    L('休息结束了。要继续吗？', 'pomo_break_end'),
    L('五分钟到了。', 'pomo_break_end'),
    L('回来吧。', 'pomo_break_end'),
    L('继续也可以，不继续也可以。', 'pomo_break_end'),

    # pomo_stop
    L('好，先停下。', 'pomo_stop'),
    L('嗯。休息一下。', 'pomo_stop'),
    L('计时取消了。', 'pomo_stop'),

    # pomo_missed
    L('你不在的时候，专注已经结束了。', 'pomo_missed'),
    L('刚才的计时过去了。', 'pomo_missed'),

    # late_night
    L('这个点了。写完这段就睡吧。', 'late_night'),
    L('夜里安静，但人也容易累。', 'late_night'),
    L('我陪你一会儿，别太久。', 'late_night'),
    L('再熬就天亮了。', 'late_night'),
    L('水杯空了。', 'late_night'),
    L('代码明天还在，你先睡。', 'late_night', 'coding'),
    L('我有点困了。……你呢。', 'late_night', 'close'),

    # late_streak
    L('这周第三次了。我不是在管你，只是……算了。', 'late_streak'),
    L('你最近总是这个点。', 'late_streak'),
    L('再这样，我要生气了。……真的。', 'late_streak'),
    L('熬夜不会让代码变好。', 'late_streak'),
    L('我明天不提醒了。……还是会提醒。', 'late_streak'),

    # meeting_end
    L('会开完了？', 'meeting_end'),
    L('刚才很安静。', 'meeting_end'),
    L('说了好多话吧。', 'meeting_end'),
    L('耳朵累不累。', 'meeting_end'),
    L('结束了就歇会儿。', 'meeting_end'),

    # care_morning
    L('早上好。今天也慢慢来。', 'care_morning'),
    L('早。先喝口热水。', 'care_morning'),
    L('醒了就好，别急着坐下。', 'care_morning', 'familiar'),

    # care_noon
    L('中午好。', 'care_noon'),
    L('到中午了，上午的事先放一放。', 'care_noon'),

    # care_afternoon
    L('下午好。困的话眯一会儿。', 'care_afternoon'),
    L('下午了，别一直绷着。', 'care_afternoon'),
    L('下午好。今天也辛苦你了。', 'care_afternoon', 'familiar'),

    # care_evening
    L('晚上好。今天辛苦了。', 'care_evening'),
    L('晚上了，收一收吧。', 'care_evening'),
    L('晚上好。别忙太晚。', 'care_evening', 'close'),

    # care_breakfast
    L('早饭吃了没？别空着肚子。', 'care_breakfast'),
    L('早上的胃得哄一下，吃点热的。', 'care_breakfast'),
    L('早饭别省。', 'care_breakfast', 'familiar'),

    # care_lunch
    L('到点了，午饭先吃。', 'care_lunch'),
    L('午饭别又凑合。', 'care_lunch'),
    L('先吃饭，活干不完的。', 'care_lunch', 'familiar'),

    # care_dinner
    L('晚饭时间到了。', 'care_dinner'),
    L('忙一天了，吃点像样的。', 'care_dinner'),
    L('先去吃饭，我等你。', 'care_dinner', 'close'),

    # care_eyes
    L('眼睛该歇会儿了。看看远处。', 'care_eyes'),
    L('闭眼十秒。就十秒。', 'care_eyes'),
    L('屏幕先放一放，眼睛会谢谢你。', 'care_eyes'),
    L('眨眨眼。你刚刚是不是又没眨。', 'care_eyes', 'familiar'),

    # care_water
    L('喝口水。', 'care_water'),
    L('杯子空了吧？去接点水。', 'care_water'),
    L('一小时了，喝两口水。', 'care_water'),
    L('别等渴了才想起来。', 'care_water', 'familiar'),

    # care_both
    L('喝口水，眼睛也歇十秒。', 'care_both'),
    L('离开屏幕一会儿吧，水和眼睛都缺。', 'care_both'),
    L('站起来，接杯水，看看窗外。', 'care_both', 'familiar'),

    # music_start
    L('这歌……不错。', 'music_start'),
    L('前奏一响，我就醒了。', 'music_start'),
    L('你放的歌，我听着。', 'music_start'),
    L('这个节奏，我喜欢。', 'music_start', 'familiar'),

    # music
    L('……副歌不错。', 'music'),
    L('别切，正听到一半。', 'music'),
    L('低音有点震。', 'music'),
    L('听着歌，时间过得快。', 'music'),
    L('你在哼什么？', 'music', 'familiar'),
    L('我想跟着晃，但会站不稳。', 'music'),
    L('这首让我想起下午。', 'music', 'close'),
    L('换一首？不换也行。', 'music'),

    # music_end
    L('歌停了。', 'music_end'),
    L('刚才那首，还行。', 'music_end'),
    L('安静下来，有点空。', 'music_end', 'close'),
    L('下次放点快的。', 'music_end', 'familiar'),
]

COMPANION_LINES += [
    # hourly
    L('{time} 了。抬头看看。', 'hourly'),
    L('{time}。要不要起来走走。', 'hourly'),
    L('又整点了。', 'hourly'),
    L('整点报时。……就一句。', 'hourly'),
    L('{time}。我还在。', 'hourly', 'close'),
    L('{time}，歇一分钟。', 'hourly'),
    L('一个钟头过去了。', 'hourly'),
    L('{time}。别一直坐着。', 'hourly'),
    L('{time}，喝口热的。', 'hourly'),
    L('时间真快。', 'hourly'),
    L('{time} 了，抱一下。', 'hourly', 'close'),
    L('{time}。你辛苦了。', 'hourly', 'familiar'),
    L('整点了。我在。', 'hourly', 'close'),
    L('{time}，偷偷提醒你。', 'hourly'),

    # sit
    L('起来一下。', 'sit'),
    L('坐太久了。', 'sit'),
    L('腰要抗议了。', 'sit'),
    L('站直一点。', 'sit'),
    L('伸伸手。', 'sit'),
    L('转个脖子。', 'sit'),
    L('走两步再回来。', 'sit'),
    L('我数到十。', 'sit'),
    L('十。', 'sit'),
    L('别赖着。', 'sit'),
    L('坐久了会变懒。', 'sit'),
    L('这是关心。', 'sit', 'close'),
    L('不是唠叨。', 'sit'),
    L('听我的。', 'sit', 'familiar'),

    # pomo_start
    L('二十五分钟。', 'pomo_start'),
    L('我陪你。', 'pomo_start', 'close'),
    L('开始。', 'pomo_start'),
    L('不看手机。', 'pomo_start'),
    L('我帮你看着时间。', 'pomo_start'),
    L('专心一点。', 'pomo_start'),
    L('需要我就在。', 'pomo_start', 'close'),
    L('加油。', 'pomo_start'),
    L('这段时间归你。', 'pomo_start'),
    L('开始吧。', 'pomo_start'),

    # pomo_break
    L('五分钟。', 'pomo_break'),
    L('休息。', 'pomo_break'),
    L('离开屏幕。', 'pomo_break'),
    L('看看窗外。', 'pomo_break'),
    L('活动一下。', 'pomo_break'),
    L('别想代码。', 'pomo_break'),
    L('可以想我。', 'pomo_break', 'familiar'),
    L('但别太想。', 'pomo_break'),
    L('休息也是任务。', 'pomo_break'),
    L('去喝口水。', 'pomo_break'),
    L('我等你回来。', 'pomo_break', 'close'),

    # pomo_end
    L('二十五分钟，结束。', 'pomo_end'),
    L('起来。', 'pomo_end'),
    L('眼睛闭一下。', 'pomo_end'),
    L('完成。', 'pomo_end'),
    L('你做到了。', 'pomo_end', 'close'),
    L('休息五分钟。', 'pomo_end'),
    L('别马上开始。', 'pomo_end'),
    L('伸个懒腰。', 'pomo_end'),
    L('我陪你休息。', 'pomo_end', 'close'),
    L('喝口水。', 'pomo_end'),
    L('看看远处。', 'pomo_end'),
    L('做得好。', 'pomo_end', 'close'),
    L('别急着证明什么。', 'pomo_end'),
    L('先照顾自己。', 'pomo_end'),

    # pomo_break_end
    L('休息完了。', 'pomo_break_end'),
    L('继续吗。', 'pomo_break_end'),
    L('准备好了就说。', 'pomo_break_end'),
    L('不急。', 'pomo_break_end'),
    L('我等你。', 'pomo_break_end', 'close'),
    L('五分钟够吗。', 'pomo_break_end'),
    L('不够就再歇会儿。', 'pomo_break_end'),
    L('开始了叫我。', 'pomo_break_end'),
    L('嗯。', 'pomo_break_end'),

    # pomo_stop
    L('停。', 'pomo_stop'),
    L('那就休息。', 'pomo_stop'),
    L('不难为你。', 'pomo_stop'),
    L('下次再来。', 'pomo_stop'),
    L('计时结束。', 'pomo_stop'),
    L('我陪着你。', 'pomo_stop', 'close'),
    L('现在可以放松了。', 'pomo_stop'),

    # pomo_missed
    L('计时过去了。', 'pomo_missed'),
    L('你不在。', 'pomo_missed'),
    L('没关系。', 'pomo_missed'),
    L('下次再说。', 'pomo_missed'),
    L('我还记着。', 'pomo_missed'),
    L('先歇着吧。', 'pomo_missed'),

    # late_night
    L('已经很晚了。', 'late_night'),
    L('该睡了。', 'late_night'),
    L('别硬撑。', 'late_night'),
    L('我陪你关电脑。', 'late_night', 'close'),
    L('明天再做。', 'late_night'),
    L('眼睛都睁不开了吧。', 'late_night'),
    L('去洗漱。', 'late_night'),
    L('我等你回来道晚安。', 'late_night', 'close'),
    L('别喝咖啡了。', 'late_night'),
    L('喝口热水。', 'late_night'),
    L('肩膀又僵了。', 'late_night'),
    L('站起来走走。', 'late_night'),
    L('夜里容易想多。', 'late_night'),
    L('别想太多。', 'late_night'),
    L('我在。', 'late_night', 'close'),
    L('睡吧。', 'late_night'),
    L('我会替你看着桌面。', 'late_night', 'familiar'),
    L('明天见。', 'late_night'),
    L('再熬我就不理你了。', 'late_night', 'familiar'),
    L('说完这句就关灯。', 'late_night'),

    # late_streak
    L('又是这个点。', 'late_streak'),
    L('这是第几次了。', 'late_streak'),
    L('我说过会提醒。', 'late_streak'),
    L('不是催你。', 'late_streak'),
    L('是担心。', 'late_streak', 'close'),
    L('你自己也知道吧。', 'late_streak'),
    L('早点睡。', 'late_streak'),
    L('明天还要用脑子。', 'late_streak'),
    L('我不说了。', 'late_streak'),
    L('但我不走。', 'late_streak', 'close'),
    L('关电脑。', 'late_streak'),
    L('听话一次。', 'late_streak', 'familiar'),

    # meeting_end
    L('开完了。', 'meeting_end'),
    L('辛苦了。', 'meeting_end'),
    L('声音都哑了吧。', 'meeting_end'),
    L('喝口水。', 'meeting_end'),
    L('起来走走。', 'meeting_end'),
    L('刚才我一句话没说。', 'meeting_end'),
    L('记我一个乖。', 'meeting_end', 'familiar'),
    L('会开得怎么样。', 'meeting_end'),
    L('不用告诉我也行。', 'meeting_end'),
    L('先歇会儿。', 'meeting_end'),
    L('眼睛累不累。', 'meeting_end'),
    L('我陪你缓一下。', 'meeting_end', 'close'),
    L('接下来还忙吗。', 'meeting_end'),
    L('别马上又开会。', 'meeting_end'),

    # care_morning
    L('早安。', 'care_morning'),
    L('新的一天。', 'care_morning'),
    L('慢慢醒。', 'care_morning'),
    L('先喝水。', 'care_morning'),
    L('吃早饭。', 'care_morning'),
    L('我等你回来。', 'care_morning', 'familiar'),
    L('今天也要好好的。', 'care_morning'),
    L('我在这儿。', 'care_morning'),

    # care_noon
    L('中午了。', 'care_noon'),
    L('该吃饭了。', 'care_noon'),
    L('先停一下。', 'care_noon'),
    L('午休一会儿。', 'care_noon'),
    L('眼睛歇歇。', 'care_noon'),
    L('别边吃边看屏幕。', 'care_noon'),
    L('我陪你吃饭。', 'care_noon', 'familiar'),
    L('吃完再说。', 'care_noon'),

    # care_afternoon
    L('下午了。', 'care_afternoon'),
    L('容易犯困吧。', 'care_afternoon'),
    L('起来走走。', 'care_afternoon'),
    L('喝口水。', 'care_afternoon'),
    L('别硬撑。', 'care_afternoon'),
    L('还有半天。', 'care_afternoon'),
    L('我陪着你。', 'care_afternoon', 'close'),
    L('慢慢来。', 'care_afternoon'),

    # care_evening
    L('晚上了。', 'care_evening'),
    L('今天结束了。', 'care_evening'),
    L('收一收。', 'care_evening'),
    L('别再加班了。', 'care_evening'),
    L('饭要好好吃。', 'care_evening'),
    L('早点休息。', 'care_evening'),
    L('我等你。', 'care_evening', 'familiar'),
    L('辛苦了。', 'care_evening', 'close'),

    # care_breakfast
    L('早饭时间。', 'care_breakfast'),
    L('吃点东西。', 'care_breakfast'),
    L('别空着肚子。', 'care_breakfast'),
    L('热乎的最好。', 'care_breakfast'),
    L('牛奶也行。', 'care_breakfast'),
    L('吃完再忙。', 'care_breakfast'),
    L('我陪你吃。', 'care_breakfast', 'familiar'),
    L('别忘了。', 'care_breakfast'),

    # care_lunch
    L('午饭时间。', 'care_lunch'),
    L('先吃饭。', 'care_lunch'),
    L('别对着屏幕吃。', 'care_lunch'),
    L('吃慢一点。', 'care_lunch'),
    L('吃饱了再想代码。', 'care_lunch', 'coding'),
    L('我等你。', 'care_lunch', 'familiar'),
    L('别凑合。', 'care_lunch'),
    L('好好吃。', 'care_lunch'),

    # care_dinner
    L('晚饭了。', 'care_dinner'),
    L('今天最后一顿。', 'care_dinner'),
    L('吃点好的。', 'care_dinner'),
    L('别省。', 'care_dinner'),
    L('慢慢吃。', 'care_dinner'),
    L('吃完散散步。', 'care_dinner'),
    L('我等你回来。', 'care_dinner', 'close'),
    L('辛苦了。', 'care_dinner'),

    # care_eyes
    L('眼睛累了。', 'care_eyes'),
    L('闭一下。', 'care_eyes'),
    L('看远处。', 'care_eyes'),
    L('十秒就好。', 'care_eyes'),
    L('眨眨眼。', 'care_eyes'),
    L('别揉了。', 'care_eyes'),
    L('热敷一下。', 'care_eyes'),
    L('我帮你数。', 'care_eyes', 'familiar'),
    L('一、二、三……', 'care_eyes'),

    # care_water
    L('喝水。', 'care_water'),
    L('杯子拿起来。', 'care_water'),
    L('温的更好。', 'care_water'),
    L('别只喝一口。', 'care_water'),
    L('喝完再忙。', 'care_water'),
    L('我提醒你了。', 'care_water'),
    L('口干了吗。', 'care_water'),
    L('去接水吧。', 'care_water'),
    L('我等你。', 'care_water', 'familiar'),

    # care_both
    L('水和眼睛都要。', 'care_both'),
    L('站起来。', 'care_both'),
    L('接杯水，看看远处。', 'care_both'),
    L('一起补。', 'care_both'),
    L('五分钟。', 'care_both'),
    L('别省这一步。', 'care_both'),
    L('我陪你。', 'care_both', 'familiar'),
    L('身体要紧。', 'care_both'),

    # music_start
    L('有歌。', 'music_start'),
    L('我听到了。', 'music_start'),
    L('这个开头不错。', 'music_start'),
    L('声音开大了。', 'music_start'),
    L('我跟着晃一下。', 'music_start'),
    L('别嫌我。', 'music_start'),
    L('这歌给你。', 'music_start', 'close'),
    L('你也喜欢吗。', 'music_start'),
    L('我听见鼓点了。', 'music_start'),
    L('可以再大声点。', 'music_start'),
    L('我不吵。', 'music_start'),
    L('听完了再说。', 'music_start'),

    # music
    L('这个拍子。', 'music'),
    L('我踩不准。', 'music'),
    L('但我努力。', 'music'),
    L('低音好听。', 'music'),
    L('人声很远。', 'music'),
    L('这首适合晚上。', 'music', 'evening'),
    L('适合发呆。', 'music'),
    L('我在数拍子。', 'music'),
    L('一、二、三、四。', 'music'),
    L('你听你的。', 'music'),
    L('我听我的。', 'music'),
    L('我们听的是一首。', 'music', 'close'),
    L('这首歌让我想动。', 'music'),
    L('又不敢动。', 'music'),
    L('怕摔。', 'music'),
    L('你扶我一下。', 'music', 'close'),
    L('下一首是什么。', 'music'),
    L('别放太吵的。', 'music'),
    L('我耳朵小。', 'music'),
    L('这首歌有点旧。', 'music'),
    L('但好听。', 'music'),
    L('你在听歌词吗。', 'music'),
    L('我在听。', 'music'),
    L('听完这句再说。', 'music'),

    # music_end
    L('放完了。', 'music_end'),
    L('再来一首？', 'music_end'),
    L('我还没听够。', 'music_end'),
    L('耳朵安静了。', 'music_end'),
    L('你累了？', 'music_end'),
    L('那就不放了。', 'music_end'),
    L('刚才那首叫什么。', 'music_end'),
    L('我想记住。', 'music_end', 'close'),
    L('下次还放这个。', 'music_end'),
    L('我等着。', 'music_end', 'familiar'),
    L('安静也挺好。', 'music_end'),
    L('你说话吧。', 'music_end'),
]
