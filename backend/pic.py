import requests
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin
from typing import Optional, List, Dict, Set
from dataclasses import dataclass, field
import time


@dataclass
class ImageConfig:
    """图片提取配置"""

    max_images: int = 3
    min_size: int = 5 * 1024  # 5KB
    headers: Dict[str, str] = field(
        default_factory=lambda: {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        }
    )
    content_selectors: Set[str] = field(
        default_factory=lambda: {
            "article",
            "main",
            ".article",
            ".content",
            ".post",
            ".entry",
            "#content",
            ".story",
        }
    )
    logo_keywords: Set[str] = field(
        default_factory=lambda: {"logo", "bd-logo", "baidu-logo", "bd_icon", "favicon"}
    )
    logo_domains: Set[str] = field(
        default_factory=lambda: {"baidu.com", "bdstatic.com"}
    )
    author_keywords: Set[str] = field(
        default_factory=lambda: {
            "author",
            "byline",
            "writer",
            "avatar",
            "usericon",
            "media-avatar",
            "reporter",
            "editor",
        }
    )
    author_selectors: Set[str] = field(
        default_factory=lambda: {
            ".qq_author",
            ".author",
            ".origin",
            ".source",
            ".byline",
            ".writer",
            ".reporter",
            ".editor",
            ".media-info",
            ".media-account",
            ".account-info",
            ".author-info",
            ".article-author",
        }
    )


class ImageExtractor:
    def __init__(self, config: Optional[ImageConfig] = None):
        self.config = config or ImageConfig()

    def extract_images(self, url: str) -> Optional[List[str]]:
        """从给定的URL中提取最多三张与内容相关的图片链接"""
        try:
            soup = self._fetch_and_parse(url)
            if not soup:
                return None

            # 查找内容区域
            content_area = next(
                (
                    area
                    for selector in self.config.content_selectors
                    if (area := soup.select_one(selector))
                ),
                soup,
            )

            # 获取作者区域（针对腾讯新闻）
            author_containers = []
            if any(domain in url for domain in ["qq.com", "tencent.com"]):
                author_containers = [
                    container
                    for selector in self.config.author_selectors
                    for container in soup.select(selector)
                ]

            # 提取并过滤图片
            candidates = self._extract_image_candidates(
                content_area, soup, author_containers, url
            )

            # 验证并选择最佳图片
            return self.validate_and_select_images(candidates)

        except Exception as e:
            print(f"❌ 提取图片失败: {str(e)}")
            return None

    def _fetch_and_parse(self, url: str) -> Optional[BeautifulSoup]:
        """获取并解析网页内容"""
        try:
            response = requests.get(url, headers=self.config.headers, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            print(f"❌ 获取页面失败: {str(e)}")
            return None

    def _extract_image_candidates(
        self,
        content_area: Tag,
        soup: BeautifulSoup,
        author_containers: List[Tag],
        base_url: str,
    ) -> List[str]:
        """提取候选图片URL"""
        # 首先在内容区域查找图片
        img_tags = content_area.find_all("img") or soup.find_all("img")

        candidates = []
        for img in img_tags:
            if src := self._get_image_src(img):
                img_url = urljoin(base_url, src)
                if (
                    img_url not in candidates
                    and not self._is_baidu_logo(img_url)
                    and not self._is_in_author_container(img, author_containers)
                ):
                    candidates.append(img_url)

            if len(candidates) >= self.config.max_images * 2:
                break

        return candidates

    def _get_image_src(self, img_tag: Tag) -> Optional[str]:
        """从img标签中提取图片URL"""
        for attr in ["src", "data-src", "data-original", "srcset"]:
            if value := img_tag.get(attr):
                return (
                    value.split(",")[0].split()[0].strip()
                    if attr == "srcset"
                    else value
                )
        return None

    def _is_baidu_logo(self, img_url: str) -> bool:
        """检测是否为百度logo"""
        if any(domain in img_url for domain in self.config.logo_domains):
            url_lower = img_url.lower()
            filename = url_lower.split("/")[-1]

            return any(
                [
                    any(keyword in url_lower for keyword in self.config.logo_keywords),
                    any(keyword in filename for keyword in self.config.logo_keywords),
                    "_logo" in filename or "logo_" in filename,
                ]
            )
        return False

    def _is_in_author_container(
        self, img_tag: Tag, author_containers: List[Tag]
    ) -> bool:
        """检查图片是否在作者信息区域内"""
        if not author_containers:
            return False

        for container in author_containers:
            if img_tag in container.find_all("img"):
                return True

            parent = img_tag.parent
            while parent and parent != img_tag.root:
                if parent in author_containers:
                    return True
                parent = parent.parent

        return False

    def validate_and_select_images(self, img_urls: List[str]) -> List[str]:
        """验证图片并选择最佳的几张"""
        valid_images = []

        for img_url in img_urls:
            try:
                head_res = requests.head(
                    img_url,
                    headers=self.config.headers,
                    timeout=5,
                    allow_redirects=True,
                )
                head_res.raise_for_status()

                if not (
                    head_res.headers.get("Content-Type", "").startswith("image/")
                    and int(head_res.headers.get("Content-Length", 0))
                    >= self.config.min_size
                    and not self._is_baidu_logo(img_url)
                ):
                    continue

                valid_images.append(img_url)
                if len(valid_images) >= self.config.max_images:
                    break

            except Exception:
                continue

        return valid_images[: self.config.max_images]

    def format_image_info(self, images: List[str]) -> str:
        """格式化图片信息"""
        if not images:
            return "未找到符合要求的图片"

        formatted = []
        for idx, img in enumerate(images, start=1):
            formatted.append(f"- 图片 {idx}: {img}")
        return "\n".join(formatted)

    def get_image_summary(self, url: str) -> list:
        """获取图片URL列表"""
        if getattr(self, "debug", False):
            # 模拟网络请求延迟
            time.sleep(2)
            return [
                "https://picsum.photos/400/300",
                "https://picsum.photos/400/301",
                "https://picsam.photos/400/303",
            ]
        return self.extract_images(url) or []
