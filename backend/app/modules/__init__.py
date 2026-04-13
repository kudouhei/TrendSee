from app.modules.trend_radar import TrendRadarModule
from app.modules.comment_mining import CommentMiningModule
from app.modules.viral_anatomy import ViralAnatomyModule
from app.modules.vertical_deep import VerticalDeepModule

MODULE_REGISTRY = {
    "trend_radar":    TrendRadarModule,
    "comment_mining": CommentMiningModule,
    "viral_anatomy":  ViralAnatomyModule,
    "vertical_deep":  VerticalDeepModule,
}

__all__ = ["TrendRadarModule", "CommentMiningModule", "ViralAnatomyModule", "VerticalDeepModule", "MODULE_REGISTRY"]
