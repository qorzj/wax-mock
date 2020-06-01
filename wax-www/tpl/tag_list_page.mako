<!DOCTYPE html>
<html>

<head>
    <meta charset='UTF-8' />
    <link rel='shortcut icon' type='image/x-icon' href='/static/favicon.ico' media='screen' />
    <!--Import Google Icon Font-->
    <link href="/static/css/icons.css" rel="stylesheet" type='text/css' />
    <!--Import materialize.css-->
    <link type="text/css" rel="stylesheet" href="/static/css/materialize.css" media="screen,projection" />
    <link href="/static/css/site.css" rel="stylesheet" type='text/css' />
    <!--Let browser know website is optimized for mobile-->
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>接口列表</title>
</head>

<body>
<ul id="slide-out" class="sidenav sidenav-fixed">
    <li>
        <div class="user-view">
            <a href="/tag/${major_tag}">${major_tag}</a>
        </div>
    </li>
    <li>
        <div class="divider"></div>
    </li>
    % for dir_key in tag_tree[major_tag]:
        <li><a class="subheader collapsible-header">${dir_key}</a></li>
        % for menu_key, menu_val in tag_tree[major_tag][dir_key].items():
        %if dir_key == dir_tag and menu_key == menu_tag:
            <li class="active">
        %else:
            <li>
        %endif
            <a class="waves-effect" href="/tag/${major_tag}-${dir_key}-${menu_key}">${menu_key}</a></li>
        % endfor
    % endfor
    <br /><br /><br /><br /><br />
</ul>
<main>
    <nav>
        <div class="nav-wrapper">
            <ul class="left">
                <li><a href="#" data-target="slide-out"
                       class="top-nav sidenav-trigger waves-effect waves-light circle hide-on-large-only"><i
                        class="material-icons">menu</i></a></li>
                % for major_i, major_key in enumerate(tag_tree):
                    <li><a href="/tag/${major_key}" style="margin-left: ${(15 * (major_i == 0))}px;">${major_key}</a></li>
                % endfor
            </ul>
            <ul id="nav-mobile" class="right hide-on-med-and-down">
                <li><a href="${git_url}" target="_blank" style="margin-right: 15px">Git</a></li>
            </ul>
        </div>
    </nav>
    <div id='contentHtml' class='container'>
        <table>
        <tbody>
        % if dir_tag in tag_tree[major_tag] and menu_tag in tag_tree[major_tag][dir_tag]:
            % for op in tag_tree[major_tag][dir_tag][menu_tag]:
                <tr>
                    <td>${op.summary}</td>
                    <td>
                    <td><span class="new badge blue">${op.method}</span></td>
                    <td>
                    <pre>${op.path}</pre>
                    </td>
                    <td>
                        <a href="javascript:void(0)" data-target="state-modal" class="modal-trigger" onclick="clear_modal('${op.operationId}')">详情</a>
                    </td>
                </tr>
            % endfor
        % endif
        </tbody>
        </table>
    </div>
    <!-- Modal Structure -->
    <div id="state-modal" class="modal">
        <div class="modal-content">
            <h4 id="modal-summary">...</h4>
            <p id="modal-desc">...</p>
            <div id="modal-basic">...</div>
            <input value="" type="hidden" id="opid-input"/>
            <div>
                <br/>
                <label for='extra-input'>extra</label>
                <textarea id="extra-input" class="materialize-textarea"></textarea>
            </div>
        </div>
        <div class="modal-footer">
            <a href="javascript:void(0)" onclick="save_state()" class="modal-close waves-effect waves-green btn-flat">保存</a>
            &nbsp;
            <a href="javascript:void(0)" class="modal-close waves-effect waves-green btn-flat">取消</a>
        </div>
    </div>
</main>

<!--JavaScript at end of body for optimized loading-->
<script src="/static/script/jquery-3.2.1.min.js"></script>
<script type="text/javascript" src="/static/script/materialize.min.js"></script>
<script type="text/javascript" src="/static/script/action/op_detail.js"></script>
<script>
    $(document).ready(function () {
        $('.sidenav').sidenav();
    });
    $(document).ready(function(){
        $('.modal').modal();
    });
    M.textareaAutoResize($('#extra-input'));
</script>
<footer class="center-align" style="margin: 15px 0;">
    <span class="grey-text text-darken-2">&copy; All rights reserved.</span>
</footer>
</body>
</html>