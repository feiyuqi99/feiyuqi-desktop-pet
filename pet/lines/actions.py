"""动作台词：伸懒腰、张望、招手、打哈欠、喝水、吃点心、打伞、看书。"""
from __future__ import annotations

from .core import L


ACTION_LINES = [
    # stretch
    L('伸个懒腰……骨头都响了。', 'action_stretch', 'familiar'),
    L('唔，坐久了，拉一拉。', 'action_stretch'),
    L('手举高一点，好像会清醒些。', 'action_stretch'),
    L('你也起来动一下吧。', 'action_stretch', 'coding'),
    L('就伸一下，不耽误你。', 'action_stretch'),
    L('肩膀有点僵。', 'action_stretch'),
    L('这样舒服多了。', 'action_stretch', 'happy'),
    L('伸完接着陪你。', 'action_stretch', 'close'),
    # look
    L('嗯？那边有什么。', 'action_look'),
    L('我看看……没什么。', 'action_look'),
    L('左看看，右看看。', 'action_look'),
    L('你是不是在偷偷摸鱼。', 'action_look', 'coding'),
    L('窗外好像亮了。', 'action_look', 'afternoon'),
    L('先看看你还在不在。', 'action_look', 'close'),
    L('没什么事，随便看看。', 'action_look'),
    L('视线对上了。', 'action_look', 'familiar'),
    # wave
    L('招招手。看见了吗。', 'action_wave'),
    L('嗨。', 'action_wave'),
    L('我在这儿呢。', 'action_wave', 'close'),
    L('不是在叫你，就是挥一下。', 'action_wave'),
    L('手举起来有点傻。', 'action_wave'),
    L('你也挥一下嘛。', 'action_wave', 'familiar'),
    L('打招呼要看着对方。', 'action_wave'),
    L('好了，放下。', 'action_wave'),
    # yawn
    L('哈啊……有点困。', 'action_yawn'),
    L('不是你的错，是午后。', 'action_yawn', 'afternoon'),
    L('打个哈欠，清醒一下。', 'action_yawn'),
    L('你也困了吗。', 'action_yawn', 'late_hours'),
    L('眼睛有点睁不开。', 'action_yawn'),
    L('再撑一会儿。', 'action_yawn', 'coding'),
    L('唔……被自己传染了。', 'action_yawn'),
    L('哈欠会传染的。', 'action_yawn', 'familiar'),
    # drink
    L('喝口水。', 'action_drink'),
    L('杯子有点凉。', 'action_drink'),
    L('你也该喝点水了。', 'action_drink', 'close'),
    L('润一下嗓子。', 'action_drink'),
    L('不急，慢慢喝。', 'action_drink'),
    L('水是温的，刚好。', 'action_drink'),
    L('喝完继续。', 'action_drink', 'coding'),
    L('你杯子空了吗。', 'action_drink'),
    # eat
    L('吃点点心。', 'action_eat'),
    L('就一小口。', 'action_eat'),
    L('你吃饭了吗。', 'action_eat', 'noon'),
    L('这块给你留着。', 'action_eat', 'close'),
    L('甜的，心情会好一点。', 'action_eat', 'low'),
    L('别光看着我。', 'action_eat', 'familiar'),
    L('吃完再干活。', 'action_eat', 'coding'),
    L('掉渣了……没事。', 'action_eat'),
    # umbrella
    L('撑会儿伞。', 'action_umbrella'),
    L('伞下有点挤。', 'action_umbrella', 'close'),
    L('要是下雨就好了。', 'action_umbrella'),
    L('太阳有点晃眼。', 'action_umbrella', 'afternoon'),
    L('你那边淋不到吧。', 'action_umbrella'),
    L('举着有点累。', 'action_umbrella'),
    L('再站一会儿。', 'action_umbrella'),
    L('收伞。', 'action_umbrella'),
    # read
    L('看会儿书。', 'action_read'),
    L('这一页看完了。', 'action_read'),
    L('你看你的，我看我的。', 'action_read', 'coding'),
    L('字有点小。', 'action_read'),
    L('安静一会儿。', 'action_read', 'familiar'),
    L('书里说……算了。', 'action_read'),
    L('翻页的声音很轻。', 'action_read'),
    L('陪你看完这页。', 'action_read', 'close'),
    # outfit
    L('这身怎么样。', 'outfit_change'),
    L('换好了，别盯太久。', 'outfit_change', 'familiar'),
    L('有点不习惯。', 'outfit_change'),
    L('你挑的，应该还行。', 'outfit_change', 'close'),
    L('转一圈给你看看。', 'outfit_change', 'happy'),
    L('会不会太花。', 'outfit_change'),
    L('先穿这个吧。', 'outfit_change'),
    L('下次换你喜欢的。', 'outfit_change', 'close'),
]
