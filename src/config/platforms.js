export const platforms = [
  { id: "tieba", name: "百度贴吧", desc: "经典贴吧系列表情包", icon: "🐾", tone: "sky", endpoint: "/assets/tieba/{id}.webp" },
  { id: "buff", name: "BUFF", desc: "网易 BUFF 系列表情包", icon: "🎯", tone: "indigo", endpoint: "/assets/buff/{id}.webp" },
  { id: "rednote", name: "小红书", desc: "小红书平台表情包", icon: "📕", tone: "red", endpoint: "/assets/rednote/{id}.webp" },
  { id: "douyin", name: "抖音", desc: "抖音平台表情包", icon: "🎵", tone: "cyan", endpoint: "/assets/douyin/{id}.webp" },
  { id: "kuaishou", name: "快手", desc: "快手平台表情包", icon: "🎥", tone: "orange", endpoint: "/assets/kuaishou/{id}.webp" },
  { id: "heybox", name: "小黑盒", desc: "小黑盒社区表情包", icon: "📦", tone: "zinc", endpoint: "/assets/heybox/{id}.webp" },
  { id: "coolapk", name: "酷安", desc: "酷安社区表情包", icon: "📱", tone: "emerald", endpoint: "/assets/coolapk/{id}.webp" },
  { id: "zhihu", name: "知乎", desc: "知乎平台表情包", icon: "📚", tone: "blue", endpoint: "/assets/zhihu/{id}.webp" },
  { id: "weibo", name: "微博", desc: "新浪微博表情包", icon: "👁️", tone: "amber", endpoint: "/assets/weibo/{id}.webp" },
  { id: "logo", name: "LOGO", desc: "各平台 Logo 资源", icon: "🕹️", tone: "violet", endpoint: "/assets/logo/{platform}.webp" },
];

export const findPlatform = (id) => platforms.find((platform) => platform.id === id);
