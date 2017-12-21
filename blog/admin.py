from django.contrib import admin

# Register your models here.
from blog.models import *

admin.site.register(UserInfo)
admin.site.register(Article)
admin.site.register(Blog)
admin.site.register(ArticleDetail)
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(Comment)
admin.site.register(CommentUp)
admin.site.register(ArticleUp)
admin.site.register(SiteArticleCategory)
admin.site.register(SiteCategory)
admin.site.register(Article2Tag)
