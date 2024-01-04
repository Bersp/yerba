from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
from mdit_py_plugins.front_matter import front_matter_plugin


def are_nodes_equal(node1, node2):
    node1_tokens = node1.to_tokens()
    node2_tokens = node2.to_tokens()
    for nt in node1_tokens+node2_tokens:
        nt.map = [0, 0]
    return node1_tokens == node2_tokens


def is_h1(node):
    return node.type == 'heading' and node.tag == 'h1'


def get_slides_md_nodes(md_file, old_md_file) -> list[dict]:
    if old_md_file is None:
        old_text = '#'
    else:
        with open(old_md_file, "r") as f:
            old_text = f.read()

    with open(md_file, "r") as f:
        text = f.read()

    md = MarkdownIt("commonmark").use(front_matter_plugin)
    tokens = md.parse(text)
    nodes = SyntaxTreeNode(tokens)

    md = MarkdownIt("commonmark").use(front_matter_plugin)
    tokens = md.parse(old_text)
    old_nodes = SyntaxTreeNode(tokens)

    old_idx = 0
    old_idx_max = len(tuple(old_nodes))-1

    idx = 0
    idx_max = len(tuple(nodes))-1

    slide_number = 0

    slides = []
    d = {'slide_number': slide_number, 'content': []}

    # TODO(bersp): Handle no title in .md or .old.*.md
    while not is_h1(nodes[idx]):
        d['content'].append(nodes[idx])
        idx += 1

    old_front_matter_content = []
    while not is_h1(old_nodes[old_idx]):
        old_front_matter_content.append(old_nodes[old_idx])
        old_idx += 1

    is_new_slide = False
    if idx != old_idx:
        is_new_slide = True
    else:
        for node, old_node in zip(d['content'], old_front_matter_content):
            if not are_nodes_equal(node, old_node):
                is_new_slide = True

    while idx < idx_max:
        node = nodes[idx]
        if is_h1(node):
            if old_idx < old_idx_max and not is_h1(old_nodes[old_idx]):
                is_new_slide = True
                # skip to the next heading
                while (old_idx != old_idx_max and
                       not is_h1(old_nodes[old_idx])):
                    old_idx += 1

            d['is_new_slide'] = is_new_slide
            slides.append(d)

            slide_number += 1
            d = {'slide_number': slide_number, 'title': node, 'content': []}

            if old_idx < old_idx_max:
                is_new_slide = not are_nodes_equal(node, old_nodes[old_idx])
                old_idx += 1
                idx += 1
            else:
                is_new_slide = True
                idx += 1

        elif old_idx > old_idx_max:
            is_new_slide = True
            d['content'].append(node)
            idx += 1

        elif are_nodes_equal(node, old_nodes[old_idx]):
            d['content'].append(node)
            old_idx += 1
            idx += 1
        else:
            is_new_slide = True

            # skip to the next heading
            while (old_idx != old_idx_max and
                   not is_h1(old_nodes[old_idx])):
                old_idx += 1
            while (idx != idx_max and
                   not is_h1(nodes[idx])):
                d['content'].append(nodes[idx])
                idx += 1

    else:
        node = nodes[idx]
        if (idx-idx_max != old_idx-old_idx_max or
                not are_nodes_equal(node, old_nodes[old_idx])):
            is_new_slide = True

    if is_h1(node):
        d['is_new_slide'] = is_new_slide
        slides.append(d)
        slide_number += 1
        d = {'slide_number': slide_number, 'title': node, 'content': []}
    else:
        d['content'].append(nodes[idx])

    d['is_new_slide'] = is_new_slide
    slides.append(d)

    return slides
