from django.contrib import admin

from rango.models import Category, Page, UserProfile

class PageAdmin(admin.ModelAdmin):
    # customising the Page page
    list_display = ('title', 'category','url','views')

# Add in this class to customise the Admin Interface
class CategoryAdmin(admin.ModelAdmin):
    # automatically populates the slug fields when type name 
    # specific variable in the admin to automate the process for us
    prepopulated_fields = {'slug':('name',)}
    list_display = ('name','views','likes','slug')

admin.site.register(Category, CategoryAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(UserProfile)