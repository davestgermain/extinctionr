# Create your models here.
from wagtail.core.blocks import (
    CharBlock, StructBlock, BooleanBlock, StructValue
)
from wagtail.embeds.blocks import EmbedBlock

class EmbedContentStructValue(StructValue):
    @property
    def thumbnail_url(self):
        from wagtail.embeds import embeds
        use_as_hero = self.get('use_as_hero')
        if not use_as_hero:
            return None
        embed = self.get('embed')
        return embeds.get_embed(embed.url).thumbnail_url


class EmbedContentBlock(StructBlock):
    embed = EmbedBlock(label="url", required=True)
    caption = CharBlock(label="caption", help_text="Enter a caption")
    use_as_hero = BooleanBlock(label="hero", help_text="Use as hero image", required=False)

    class Meta:
        icon = 'site'
        value_class = EmbedContentStructValue
        template = 'blocks/embed_block.html'


