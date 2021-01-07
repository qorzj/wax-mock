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
    <title>${op['summary']}-接口详情</title>
    <style>
        .tooltip-font {
            color: #B71C1C;
        }
    </style>
</head>

<body>
<ul id="slide-out" class="sidenav sidenav-fixed">
    <li>
        <div class="user-view">
            标签列表
        </div>
    </li>
    <li>
        <div class="divider"></div>
    </li>
    % for tag in op.get('tags', []):
        <li>
        <a class="waves-effect" href="/tag/${tag}">${tag}</a>
        </li>
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
                % for major_i, major_key in enumerate(x for x in tag_tree if x != 'API'):
                    <li><a href="/tag/${major_key}" style="margin-left: ${(15 * (major_i == 0))}px;">${major_key}</a></li>
                % endfor
            </ul>
            <ul id="nav-mobile" class="right hide-on-med-and-down">
                <li><a href="${git_url}" target="_blank" style="margin-right: 15px">Git</a></li>
            </ul>
        </div>
    </nav>
    <div id='contentHtml' class='container'>
        <h4>${op['summary']}</h4>
        <div>
            <pre><span style="color: #0D47A1">${method}</span> ${path}   <a href="${mock_prefix}${path}">Mock地址</a> <a href="javascript:void(0)" data-target="state-modal" class="btn-flat btn-small modal-trigger" onclick="clear_modal('${op['operationId']}')">切换example</a></pre>
        </div>
        <div><pre><strong>接口ID:</strong> ${op['operationId']}</pre></div>
        % if 'description' in op:
            <div><strong>接口描述:</strong></div>
            <div><pre>${op['description']}</pre></div>
        % endif
        <hr style="margin-top: 20px"/>
        <h5 style="border-left: 3px solid #0D47A1; padding-left: 6px">请求参数</h5>
        % for source in ['Path', 'Query', 'Header']:
        % if params.get(source.lower()):
            <div style="margin-top: 20px; margin-bottom: 10px"><strong>${source}:</strong></div>
            <table class="striped"><tbody>
            % for item in params[source.lower()]:
                <tr>
                    <td style="width: 30%">${item['name']}</td>
                    % if len(item.get('schema', {})) > 1:
                        <td><span class="tooltipped tooltip-font" data-position="bottom" data-tooltip="${item.get('schema')}">${item.get('schema', {}).get('type', '')}${(' !' if item.get('required') else '')}</span></td>
                    % else:
                        <td><span>${item.get('schema', {}).get('type', '')}${(' !' if item.get('required') else '')}</span></td>
                    % endif
                    <td style="width: 50%; text-align: center">${item.get('description', '')}</td>
                    <td><span>(${('必传' if item.get('required') else '非必传')})</span></td>
                </tr>
            % endfor
            </tbody></table>
        % endif
        % endfor
        % if requests:
            <div style="margin-top: 20px; margin-bottom: 10px"><strong>Body:</strong></div>
            % for request in requests:
                <div style="margin-top: 20px; margin-bottom: 10px"><strong>Content-Type:</strong> ${request['content_type']}</div>
                <table class="striped"><tbody>
                    % for item in request['rows']:
                        <tr>
                            <td style="width: 30%"><span style="margin-left: ${(20 * item['level'].count('/') - 20)}px;">${item['name']}</span></td>
                            % if item.get('additional'):
                                <td><span class="tooltipped tooltip-font" data-position="bottom" data-tooltip="${item.get('additional')}">${' '.join(item['types'])}</span></td>
                            % else:
                                <td><span>${' '.join(item['types'])}</span></td>
                            % endif
                            <td style="width: 50%; text-align: center">${item.get('description', '')}</td>
                        </tr>
                    % endfor
                </tbody></table>
            % endfor
        % endif
        <hr style="margin-top: 20px"/>
        <h5 style="border-left: 3px solid #0D47A1; padding-left: 6px">返回数据</h5>
        % for resp_index, response in enumerate(responses):
            <div style="margin-top: 20px; margin-bottom: 10px">
                <strong>Status Code:</strong> ${response['status_code']}<br/>
                <strong>Content-Type:</strong> ${response['content_type']}<br/>
                <strong>Examples:</strong>
                % for example_key in response['examples'].keys():
                    &nbsp; <a href="javascript:void(0)" data-target="example-modal" class="modal-trigger"
                              onclick="show_example('${op['operationId']}', ${resp_index}, '${example_key}')">${example_key}</a>
                % endfor
            </div>
            <table class="striped"><tbody>
                % for item in response['rows']:
                    <tr>
                        <td style="width: 30%"><span style="margin-left: ${(20 * item['level'].count('/') - 20)}px;">${item['name']}</span></td>
                        % if item.get('additional'):
                            <td><span class="tooltipped tooltip-font" data-position="bottom" data-tooltip="${item.get('additional')}">${' '.join(item['types'])}</span></td>
                        % else:
                            <td><span>${' '.join(item['types'])}</span></td>
                        % endif
                        <td style="width: 50%; text-align: center">${item.get('description', '')}</td>
                    </tr>
                % endfor
            </tbody></table>
        % endfor
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
    <div id="example-modal" class="modal">
        <div class="modal-content">
            <pre id="example-value">...</pre>
        </div>
        <div class="modal-footer">
            <a href="javascript:void(0)" class="modal-close waves-effect waves-green btn-flat">确定</a>
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
        $('.tooltipped').tooltip();
    });
    $(document).ready(function(){
        $('.modal').modal();
    });
    M.textareaAutoResize($('#extra-input'));
</script>
<footer class="center-align" style="margin: 15px 0;">
    <span class="grey-text text-darken-2">&copy; All rights reserved.
        &nbsp; <a href="/static/mockjs.html">Mockjs</a>
        &nbsp; <a href="/static/pql.html">PQL</a>
        &nbsp; <a href="/openapi.json">openapi</a>
        &nbsp; <a href="/openapi.kt">kotlin</a>
        &nbsp; <a href="/solution.md">solution</a>
    </span>
</footer>
</body>
</html>