render = function(data, env) {
    return {
        block: 'b-page',
        title: data['title']('Page title'),
        head: [
            { elem: 'css', url: '/static/example.css'},
            { elem: 'css', url: '/static/example.ie.css', ie: 'lt IE 8' },
            { block: 'i-jquery', elem: 'core' },
            { elem: 'js', url: '/static/example.js' }
        ],
        content: [
            {
                block: 'b-link',
                mods : { pseudo : 'yes', togcolor : 'yes', color: 'green' },
                url: '#',
                target: '_blank',
                title: 'button',
                content: data['text']
            },
        ]
    }
}
