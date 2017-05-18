def create_image_tag_str(source, width, height):
    """
    Create an image tag that could be embedded into a table contents.

    The image's width and height and required since mxgraph will render the
    html in a helper container in order to get the cell's size. To avoid the
    cell size to be wrongly calculated we got some options like passing the
    image's size explicitly (as done here) or force the user to pre load the
    images so when rendering the html the image is already loaded and the
    correct size is used.

    :param str source: The URL to the image, data URIs can be used.
    :param int width: The desired width for the image.
    :param int height: The desired height for the image.
    :rtype: str
    """
    tag_template = '<img src="{source}" width="{width}" height="{height}" />'
    if source.find('"') != -1:
        raise ValueError('source argument can not have the " character')
    width = int(width)
    height = int(height)
    return tag_template.format(source=source, width=width, height=height)
