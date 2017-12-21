from django.shortcuts import render, HttpResponse, redirect
from django.db import transaction
from django import forms
# Create your views here.
from blog.forms import *
from blogCMS import settings
from django.db.models import F
from blog import forms
from django.db.models import Count
from django.http import JsonResponse
from django.contrib import auth
import datetime
import json



def login(request):
    # if request.is_ajax():

    if request.is_ajax():

        username = request.POST.get("username")
        password = request.POST.get("password")
        validCode = request.POST.get("validCode")

        login_response = {"is_login": False, "error_msg": None}

        if validCode.upper() == request.session.get("keepValidCode").upper():
            user = auth.authenticate(username=username, password=password)
            if user:
                login_response["is_login"] = True
                auth.login(request, user)

            else:
                login_response["error_msg"] = "username or password error"

        else:
            login_response["error_msg"] = 'validCode error'

        import json

        return HttpResponse(json.dumps(login_response))

    return render(request, "login.html")


def get_validCode_img(request):
    # 方式1：
    # import os
    # path= os.path.join(settings.BASE_DIR,"blog","static","img","egon.jpg")
    #
    # with open(path,"rb") as f:
    #     data=f.read()

    # 方式2：
    # from  PIL import Image
    #
    # img=Image.new(mode="RGB",size=(120,40),color="green")
    #
    # f=open("validCode.png","wb")
    # img.save(f,"png")
    #
    # with open("validCode.png","rb") as f:
    #     data=f.read()

    # 方式3：
    # from io import BytesIO
    #
    # from PIL import Image
    # img = Image.new(mode="RGB", size=(120, 40), color="blue")
    # f=BytesIO()
    # img.save(f,"png")
    # data=f.getvalue()
    # return HttpResponse(data)

    # 方式4 ：

    from io import BytesIO
    import random

    from PIL import Image, ImageDraw, ImageFont
    img = Image.new(mode="RGB", size=(120, 40),
                    color=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))

    draw = ImageDraw.Draw(img, "RGB")
    font = ImageFont.truetype("blog/static/font/kumo.ttf", 25)

    valid_list = []
    for i in range(5):

        random_num = str(random.randint(0, 9))
        random_lower_zimu = chr(random.randint(65, 90))
        random_upper_zimu = chr(random.randint(97, 122))

        random_char = random.choice([random_num, random_lower_zimu, random_upper_zimu])
        draw.text([5 + i * 24, 10], random_char,
                  (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), font=font)
        for i in range(50):
            draw.point([random.randint(0, 120), random.randint(0, 40)],
                       fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        valid_list.append(random_char)

    f = BytesIO()
    img.save(f, "png")
    data = f.getvalue()

    valid_str = "".join(valid_list)
    print(valid_str)

    request.session["keepValidCode"] = valid_str

    return HttpResponse(data)


def index(request, *args, **kwargs):
    if kwargs:
        article_list = models.Article.objects.filter(site_article_category__name=kwargs.get("site_article_category"))
    else:
        article_list = models.Article.objects.all()
    cate_list = models.SiteCategory.objects.all()
    return render(request, "index.html", {"article_list": article_list, "cate_list": cate_list})


def log_out(request):
    auth.logout(request)

    return redirect("/login/")


def article(request):
    return render(request, "article.html")


def reg(request):
    if request.is_ajax():
        form_obj = forms.RegForm(request, request.POST)

        regResponse = {"user": None, "errorsList": None}
        if form_obj.is_valid():

            username = form_obj.cleaned_data["username"]
            password = form_obj.cleaned_data["password"]
            email = form_obj.cleaned_data.get("email")
            avatar_img = request.FILES.get("avatar_img")

            user_obj = models.UserInfo.objects.create_user(username=username, password=password, email=email,
                                                           avatar=avatar_img, nickname=username)
            regResponse["user"] = user_obj.username

        else:
            regResponse["errorsList"] = form_obj.errors
        import json
        return HttpResponse(json.dumps(regResponse))

    form_obj = forms.RegForm(request)
    return render(request, "reg.html", {"form_obj": form_obj})


def homeSite(request, username, **kwargs):
    current_user = models.UserInfo.objects.filter(username=username).first()
    current_blog = current_user.blog
    if not current_user:
        return render(request, "notFound.html")
    '''查询当前用户的所有文章'''
    article_list = models.Article.objects.filter(user=current_user)
    '''查询 当前用户的分类归档'''

    category_list = models.Category.objects.all().filter(blog=current_blog).annotate(
        c=Count("article__nid")).values_list("title", "c")
    print('..........', category_list)
    '''查询当前用户的标签归档'''
    tag_list = models.Tag.objects.all().filter(blog=current_blog).annotate(c=Count("article__nid")).values_list("title",
                                                                                                                "c")

    '''查询当前用户的日期归档'''
    date_list = models.Article.objects.filter(user=current_user).extra(
        select={"filter_create_date": "strftime('%%Y/%%m',create_time)"}).values_list("filter_create_date").annotate(
        Count("nid"))
    if kwargs:
        if kwargs.get("condition") == "category":
            article_list = models.Article.objects.filter(user=current_user, category__title=kwargs.get("para"))
        elif kwargs.get("condition") == "tag":
            article_list = models.Article.objects.filter(user=current_user, tags__title=kwargs.get("para"))
        elif kwargs.get("condition") == "date":
            year, month = kwargs.get("para").split("/")
            article_list = models.Article.objects.filter(user=current_user, create_time__year=year,
                                                         create_time__month=month)

    return render(request, "homeSite.html", locals())


def articleDetail(request,username,article_id):
    print("rrrrrrrrrrrrrrrrrrrrrr")
    current_user = models.UserInfo.objects.filter(username=username).first()
    current_blog = current_user.blog
    if not current_user:
        return render(request, 'notFound.html')

    # 查询当前用户所有文章

    article_list = models.Article.objects.filter(user=current_user)

    # 查询 当前用户的分类归档
    from django.db.models import Count, Sum

    category_list = models.Category.objects.all().filter(blog=current_blog).annotate(
        c=Count("article__nid")).values_list("title", "c")


    # 查询当前用户的标签归档

    tag_list = models.Tag.objects.all().filter(blog=current_blog).annotate(c=Count("article__nid")).values_list("title",
                                                                                                                "c")


    # 查询当前用户的日期归档

    date_list = models.Article.objects.filter(user=current_user).extra(
        select={"filter_create_date": "strftime('%%Y/%%m',create_time)"}).values_list("filter_create_date").annotate(
        Count("nid"))
    print(date_list)



    article_obj=models.Article.objects.filter(nid=article_id).first()
    comment_list=models.Comment.objects.filter(article_id=article_id)#找出这篇文章里面的所有评论
    return render(request,"article_detail.html",locals())
def poll(request):
    print(11)

    user_id=request.user.nid
    article_id=request.POST.get("article_id")
    pollResponse={"state":True,"is_repeat":None}
    if models.ArticleUp.objects.filter(user_id=user_id, article_id=article_id):
        print(22)
        pollResponse["state"]=False
        pollResponse["is_repeat"]=True

    else:

        try:
            with transaction.atomic():
                articleUp = models.ArticleUp.objects.create(user_id=user_id, article_id=article_id)
                models.Article.objects.filter(nid=article_id).update(up_count=F("up_count") + 1)
        except:

            pollResponse["state"] = False

    import json
    return HttpResponse(json.dumps(pollResponse))
def comment(request):

    article_id=request.POST.get("article_id")
    comment_content=request.POST.get("comment_content")
    user_id=request.user.nid

    commentResponse={}
    print(request.POST.get("parent_comment_id"),"=======")
    if request.POST.get("parent_comment_id"):    #   处理子评论
        with transaction.atomic():
            pid=request.POST.get("parent_comment_id")
            comment_obj=models.Comment.objects.create(article_id=article_id,user_id=user_id,content=comment_content,parent_comment_id=pid)
            commentResponse["parent_comment_username"]=comment_obj.parent_comment.user.username
            commentResponse["parent_comment_content"]=comment_obj.parent_comment.content

    else:   #  处理的文章评论，即根评论
        with transaction.atomic():

            comment_obj=models.Comment.objects.create(article_id=article_id,user_id=user_id,content=comment_content)
            models.Article.objects.filter(nid=article_id).update(comment_count=F("comment_count")+1)



    commentResponse["create_time"] = str(comment_obj.create_time)
    commentResponse["comment_id"] = comment_obj.nid

    return JsonResponse(commentResponse)
def commentTree(request,article_id):


    comment_list=models.Comment.objects.filter(article_id=article_id).values("nid","content","parent_comment_id")
    print(comment_list)

    comment_dict = {}

    for comment in comment_list:
        comment["chidren_commentList"] = []
        comment_dict[comment["nid"]] = comment



    #====================================找父评论====================================================

    commentTree = []

    for comment in comment_list:  # comment :  {'id': 1, 'content': '...', 'Pid': None, 'chidren_commentList': [{'id': 5, 'content': '...', 'Pid': 1, 'chidren_commentList': []},]},
        pid = comment.get("parent_comment_id")
        if pid:
            print(comment)  # {'id': 4, 'content': '...', 'Pid': 1, 'chidren_commentList': []}
            comment_dict[pid]["chidren_commentList"].append(comment)
        else:
            commentTree.append(comment)

    print(commentTree)
    import json
    return HttpResponse(json.dumps(commentTree))
def backendIndex(request):
    if not request.user.is_authenticated():
        return redirect("/login/")
    article_list = models.Article.objects.filter(user=request.user).all()
    return render(request, "backendindex.html", {"article_list": article_list})
def addArticle(request):

    if request.method=="POST":
        article_form = ArticleForm(request.POST)
        if article_form.is_valid():
            title=article_form.cleaned_data.get("title")
            content=article_form.cleaned_data.get("content")
            article_obj=models.Article.objects.create(title=title,desc=content[0:30],create_time=datetime.datetime.now(),user=request.user)
            models.ArticleDetail.objects.create(content=content,article=article_obj)
        else:
            pass

        return HttpResponse("添加成功")

    article_form=ArticleForm()
    return render(request,"addArticle.html",{"article_form":article_form})
def uploadFile(request):
    print("POST",request.POST)
    print("FILES",request.FILES)
    file_obj=request.FILES.get("imgFile")
    file_name=file_obj.name

    from blogCMS import settings
    import os
    path=os.path.join(settings.MEDIA_ROOT,"article_uploads",file_name)
    with open(path,"wb") as f:
        for i in file_obj.chunks():
            f.write(i)

    response={
        "error":0,
        "url":"/media/article_uploads/"+file_name+"/"

    }

    import json
    return HttpResponse(json.dumps(response))
#滑动验证码
from blog.geetest import GeetestLib

pc_geetest_id = "b46d1900d0a894591916ea94ea91bd2c"
pc_geetest_key = "36fc3fe98530eea08dfc6ce76e3d24c4"
mobile_geetest_id = "7c25da6fe21944cfe507d2f9876775a9"
mobile_geetest_key = "f5883f4ee3bd4fa8caec67941de1b903"

def pcgetcaptcha(request):
    user_id = 'test'
    gt = GeetestLib(pc_geetest_id, pc_geetest_key)
    status = gt.pre_process(user_id)
    request.session[gt.GT_STATUS_SESSION_KEY] = status
    request.session["user_id"] = user_id
    response_str = gt.get_response_str()
    return HttpResponse(response_str)


def pcajax_validate(request):
    if request.method == "POST":
        login_response = {"is_login": False, "error_msg": None}
        #  验证验证码
        gt = GeetestLib(pc_geetest_id, pc_geetest_key)
        challenge = request.POST.get(gt.FN_CHALLENGE, '')
        validate = request.POST.get(gt.FN_VALIDATE, '')
        seccode = request.POST.get(gt.FN_SECCODE, '')
        status = request.session[gt.GT_STATUS_SESSION_KEY]
        user_id = request.session["user_id"]
        if status:
            result = gt.success_validate(challenge, validate, seccode, user_id)
        else:
            result = gt.failback_validate(challenge, validate, seccode)
        # 扩充 验证用户名密码
        if result:
            username = request.POST.get("username")
            password = request.POST.get("password")

            user = auth.authenticate(username=username, password=password)
            if user:
                login_response["is_login"] = True
                auth.login(request, user)

            else:
                login_response["error_msg"] = "username or password error"

        else:
            login_response["error_msg"]="验证码错误"

        return HttpResponse(json.dumps(login_response))





    return HttpResponse("error")