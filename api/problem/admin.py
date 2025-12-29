from django.contrib import admin
from .models import (
    Problem, Codeblock, Testcase, Solution, 
    Tags, ProblemTags, Discuss, DiscussTags
)


class CodeblockInline(admin.TabularInline):
    model = Codeblock
    extra = 1
    fields = ('imports','block', 'runner_code', 'language')


class TestcaseInline(admin.TabularInline):
    model = Testcase
    extra = 1
    readonly_fields = ('id', 'created_at')
    fields = ('input', 'output', 'display_testcase', 'created_at')


class ProblemTagsInline(admin.TabularInline):
    model = ProblemTags
    extra = 1


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('id', 'name', 'problem_description')
    readonly_fields = ('id', 'created_at')
    inlines = [CodeblockInline, TestcaseInline, ProblemTagsInline]
    
    fieldsets = (
        (None, {'fields': ('id', 'name', 'problem_description')}),
        ('Metadata', {'fields': ('created_at',)}),
    )
    
    def get_description_preview(self, obj):
        return obj.problem_description[:100] + '...' if len(obj.problem_description) > 100 else obj.problem_description
    get_description_preview.short_description = 'Description'


@admin.register(Codeblock)
class CodeblockAdmin(admin.ModelAdmin):
    list_display = ('id', 'problem', 'language', 'get_block_preview')
    list_filter = ('problem', 'language')
    search_fields = ('problem__id', 'imports', 'block', 'runner_code')
    readonly_fields = ('id',)
    raw_id_fields = ('problem',)
    
    def get_block_preview(self, obj):
        return obj.block[:100] + '...' if len(obj.block) > 100 else obj.block
    get_block_preview.short_description = 'Code Block'


@admin.register(Testcase)
class TestcaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'problem', 'created_at')
    list_filter = ('created_at', 'problem')
    search_fields = ('problem__id', 'input', 'output', 'display_testcase')
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('problem',)
    
    fieldsets = (
        (None, {'fields': ('id', 'problem', 'input', 'output', 'display_testcase')}),
        ('Metadata', {'fields': ('created_at',)}),
    )


@admin.register(Solution)
class SolutionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'problem', 'language', 'status', 'created_at')
    list_filter = ('status', 'language', 'created_at', 'problem')
    search_fields = ('user__username', 'problem__id')
    readonly_fields = ('id', 'created_at', 'status')
    raw_id_fields = ('user', 'problem')
    
    fieldsets = (
        (None, {'fields': ('id', 'user', 'problem', 'code', 'language')}),
        ('Status', {'fields': ('status',)}),
        ('Metadata', {'fields': ('created_at',)}),
    )
    
    def get_readonly_fields(self, request, obj=None):
        # Make status readonly only for existing objects (after submission)
        if obj:
            return self.readonly_fields
        return ('id', 'created_at')


@admin.register(Tags)
class TagsAdmin(admin.ModelAdmin):
    list_display = ('id', 'tags')
    search_fields = ('tags',)
    readonly_fields = ('id',)


@admin.register(ProblemTags)
class ProblemTagsAdmin(admin.ModelAdmin):
    list_display = ('problem', 'tag')
    list_filter = ('tag',)
    search_fields = ('problem__id', 'tag__tags')
    raw_id_fields = ('problem', 'tag')


class DiscussTagsInline(admin.TabularInline):
    model = DiscussTags
    extra = 1


@admin.register(Discuss)
class DiscussAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'problem', 'created_at')
    list_filter = ('created_at', 'problem')
    search_fields = ('title', 'body', 'author__username')
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('author', 'problem', 'user')
    inlines = [DiscussTagsInline]
    
    fieldsets = (
        (None, {'fields': ('id', 'title', 'body')}),
        ('Relations', {'fields': ('author', 'user', 'problem')}),
        ('Metadata', {'fields': ('created_at',)}),
    )


@admin.register(DiscussTags)
class DiscussTagsAdmin(admin.ModelAdmin):
    list_display = ('discuss', 'tag')
    list_filter = ('tag',)
    search_fields = ('discuss__title', 'tag__tags')
    raw_id_fields = ('discuss', 'tag')