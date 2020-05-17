from wagtail.core.blocks import (
    CharBlock, StructBlock, ListBlock
)
from wagtail.images.blocks import ImageChooserBlock

class ImageCarouselBlock(ListBlock):

    def __init__(self):
        super().__init__(StructBlock([
            ('image', ImageChooserBlock()),
            ('caption', CharBlock(max_length=255, required=False)),
        ]))

    class Meta:
        icon = 'image'
        template = 'blocks/image_carousel_block.html'
