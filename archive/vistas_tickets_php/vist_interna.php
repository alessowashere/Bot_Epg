<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html lang="es-MX">
<head>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
    <meta http-equiv="cache-control" content="no-cache" />
    <meta http-equiv="pragma" content="no-cache" />
    <meta http-equiv="x-pjax-version" content="0375576">
    <title>Ticket #230205</title>
    <!--[if IE]>
    <style type="text/css">
        .tip_shadow { display:block !important; }
    </style>
    <![endif]-->
    <script type="text/javascript" src="/js/jquery-3.7.0.min.js?0375576"></script>
    <link rel="stylesheet" href="/css/thread.css?0375576" media="all"/>
    <link rel="stylesheet" href="/scp/css/scp.css?0375576" media="all"/>
    <link rel="stylesheet" href="/css/redactor.css?0375576" media="screen"/>
    <link rel="stylesheet" href="/css/typeahead.css?0375576" media="screen"/>
    <link type="text/css" href="/css/ui-lightness/jquery-ui-1.13.2.custom.min.css?0375576"
         rel="stylesheet" media="screen" />
    <link rel="stylesheet" href="/css/jquery-ui-timepicker-addon.css?0375576" media="all"/>
    <link type="text/css" rel="stylesheet" href="/css/font-awesome.min.css?0375576"/>
    <!--[if IE 7]>
    <link rel="stylesheet" href="/css/font-awesome-ie7.min.css?0375576"/>
    <![endif]-->
    <link type="text/css" rel="stylesheet" href="/scp/css/dropdown.css?0375576"/>
    <link type="text/css" rel="stylesheet" href="/css/loadingbar.css?0375576"/>
    <link type="text/css" rel="stylesheet" href="/css/flags.css?0375576"/>
    <link type="text/css" rel="stylesheet" href="/css/select2.min.css?0375576"/>
    <link type="text/css" rel="stylesheet" href="/css/rtl.css?0375576"/>
    <link type="text/css" rel="stylesheet" href="/scp/css/translatable.css?0375576"/>
    <!-- Favicons -->
    <link rel="icon" type="image/png" href="/images/oscar-favicon-32x32.png" sizes="32x32" />
    <link rel="icon" type="image/png" href="/images/oscar-favicon-16x16.png" sizes="16x16" />

    
	<meta name="csrf_token" content="9d44856b3c4571060e82017964a25cbbe4c635fb" />
	<script type="text/javascript" src="js/ticket.js?0375576"></script>
	<script type="text/javascript" src="js/thread.js?0375576"></script>
	<meta name="tip-namespace" content="tickets.queue" />
</head>
<body>
<div id="container">
        <div id="header">
        <p id="info" class="pull-right no-pjax">Bienvenido, <strong>Escuela de Posgrado</strong>.                       | <a href="/scp/index.php" class="no-pjax">Panel de agente</a>
                        | <a href="/scp/profile.php">Perfil</a>
            | <a href="/scp/logout.php?auth=876e6e6de49db0532cdab656d3a00559" class="no-pjax">Salir</a>
        </p>
        <a href="/scp/index.php" class="no-pjax" id="logo">
            <span class="valign-helper"></span>
            <img src="/scp/logo.php?1755016331" alt="osTicket &mdash; Sistema de soporte al cliente"/>
        </a>
    </div>
    <div id="pjax-container" class="">
    <ul id="nav">
<li class="inactive no-pjax"><a href="/scp/dashboard.php">Panel de Control</a><ul>
<li><a class="logs" href="/scp/dashboard.php" title="" id="">Panel de Control</a></li><li><a class="teams" href="/scp/directory.php" title="" id="">Directorio del agente</a></li><li><a class="users" href="/scp/profile.php" title="" id="">Mi perfil</a></li>
</ul>

</li>
<li class="inactive "><a href="/scp/tasks.php">Tareas</a><ul>
<li><a class="Ticket" href="/scp/tasks.php" title="" id="">Tareas</a></li>
</ul>

</li>
<li class="active "><a href="/scp/tickets.php">Solicitudes</a>
</li>
<li class="inactive "><a href="/scp/kb.php">Base de conocimientos</a><ul>
<li><a class="kb" href="/scp/kb.php" title="" id="">FAQs</a></li><li><a class="canned" href="/scp/canned.php" title="" id="">Respuestas Predefinidas</a></li>
</ul>

</li>
    </ul>
    <nav class="" id="customQ_nav">
  <ul id="sub_nav">
<li class="top-queue item ">
  <a href="tickets.php?queue=1"
    class="Ticket"><i class="small icon-sort-down pull-right"></i>Abierto  </a>
  <div class="customQ-dropdown">
    <ul class="scroll-height">
      <!-- Add top-level queue (with count) -->

            <!-- Start Dropdown and child queues -->
      <!-- SubQ class: only if top level Q has subQ -->
<li >

  <span class="    pull-right newItemQ queue-count"
    data-queue-id="2"><span class="faded-more">-</span>
  </span>

  <a class="truncate " href="tickets.php?queue=2" title="Open">
      Open          </a>

    </li>
<!-- SubQ class: only if top level Q has subQ -->
<li >

  <span class="    pull-right newItemQ queue-count"
    data-queue-id="3"><span class="faded-more">-</span>
  </span>

  <a class="truncate " href="tickets.php?queue=3" title="Answered">
      Answered          </a>

    </li>
<!-- SubQ class: only if top level Q has subQ -->
<li >

  <span class="    pull-right newItemQ queue-count"
    data-queue-id="4"><span class="faded-more">-</span>
  </span>

  <a class="truncate " href="tickets.php?queue=4" title="Overdue">
      Overdue          </a>

    </li>
    </ul>
    <!-- Add Queue button sticky at the bottom -->
    <div class="add-queue">
      <a class="full-width" onclick="javascript:
        var pid = 1;
        $.dialog('ajax.php/tickets/search?parent_id='+pid, 201);">
        <span><i class="green icon-plus-sign"></i>
          Agregar cola personal</span>
      </a>
    </div>
  </div>
</li>
<li class="top-queue item ">
  <a href="tickets.php?queue=5"
    class="Ticket"><i class="small icon-sort-down pull-right"></i>Mis Tickets  </a>
  <div class="customQ-dropdown">
    <ul class="scroll-height">
      <!-- Add top-level queue (with count) -->

            <!-- Start Dropdown and child queues -->
      <!-- SubQ class: only if top level Q has subQ -->
<li >

  <span class="    pull-right newItemQ queue-count"
    data-queue-id="6"><span class="faded-more">-</span>
  </span>

  <a class="truncate " href="tickets.php?queue=6" title="Assigned to Me">
      Assigned to Me          </a>

    </li>
<!-- SubQ class: only if top level Q has subQ -->
<li >

  <span class="    pull-right newItemQ queue-count"
    data-queue-id="7"><span class="faded-more">-</span>
  </span>

  <a class="truncate " href="tickets.php?queue=7" title="Assigned to Teams">
      Assigned to Teams          </a>

    </li>
    </ul>
    <!-- Add Queue button sticky at the bottom -->
    <div class="add-queue">
      <a class="full-width" onclick="javascript:
        var pid = 5;
        $.dialog('ajax.php/tickets/search?parent_id='+pid, 201);">
        <span><i class="green icon-plus-sign"></i>
          Agregar cola personal</span>
      </a>
    </div>
  </div>
</li>
<li class="top-queue item ">
  <a href="tickets.php?queue=8"
    class="Ticket"><i class="small icon-sort-down pull-right"></i>Cerrado  </a>
  <div class="customQ-dropdown">
    <ul class="scroll-height">
      <!-- Add top-level queue (with count) -->

            <!-- Start Dropdown and child queues -->
      <!-- SubQ class: only if top level Q has subQ -->
<li >

  <span class="    pull-right newItemQ queue-count"
    data-queue-id="9"><span class="faded-more">-</span>
  </span>

  <a class="truncate " href="tickets.php?queue=9" title="Today">
      Today          </a>

    </li>
<!-- SubQ class: only if top level Q has subQ -->
<li >

  <span class="    pull-right newItemQ queue-count"
    data-queue-id="10"><span class="faded-more">-</span>
  </span>

  <a class="truncate " href="tickets.php?queue=10" title="Yesterday">
      Yesterday          </a>

    </li>
<!-- SubQ class: only if top level Q has subQ -->
<li >

  <span class="    pull-right newItemQ queue-count"
    data-queue-id="11"><span class="faded-more">-</span>
  </span>

  <a class="truncate " href="tickets.php?queue=11" title="This Week">
      This Week          </a>

    </li>
<!-- SubQ class: only if top level Q has subQ -->
<li >

  <span class="    pull-right newItemQ queue-count"
    data-queue-id="12"><span class="faded-more">-</span>
  </span>

  <a class="truncate " href="tickets.php?queue=12" title="This Month">
      This Month          </a>

    </li>
<!-- SubQ class: only if top level Q has subQ -->
<li >

  <span class="    pull-right newItemQ queue-count"
    data-queue-id="13"><span class="faded-more">-</span>
  </span>

  <a class="truncate " href="tickets.php?queue=13" title="This Quarter">
      This Quarter          </a>

    </li>
<!-- SubQ class: only if top level Q has subQ -->
<li >

  <span class="    pull-right newItemQ queue-count"
    data-queue-id="14"><span class="faded-more">-</span>
  </span>

  <a class="truncate " href="tickets.php?queue=14" title="This Year">
      This Year          </a>

    </li>
    </ul>
    <!-- Add Queue button sticky at the bottom -->
    <div class="add-queue">
      <a class="full-width" onclick="javascript:
        var pid = 8;
        $.dialog('ajax.php/tickets/search?parent_id='+pid, 201);">
        <span><i class="green icon-plus-sign"></i>
          Agregar cola personal</span>
      </a>
    </div>
  </div>
</li>
<li class="primary-only item ">
  <a class="Ticket" href="#" data-dialog="ajax.php/tickets/search"><i class="icon-sort-down pull-right"></i>Buscar</a>
  <div class="customQ-dropdown">
    <ul class="scroll-height">
      <!-- Start Dropdown and child queues -->
               </ul>
    <!-- Add Queue button sticky at the bottom -->

     <div class="add-queue">
      <a class="full-width" onclick="javascript:
        $.dialog('ajax.php/tickets/search', 201);">
        <span><i class="green icon-plus-sign"></i>
          Agregar búsqueda personal</span>
      </a>
    </div>
  </div>
</li>
<li><a class="newTicket" href="tickets.php?a=open" title="Abrir un nuevo Ticket" id="new-ticket" >Nuevo Ticket</a></li>  </ul>
</nav>

        <div id="content">
        <div>
    <div id="msg_notice" style="display: none;"><span id="msg-txt"></span></div>
    <div class="sticky bar">
       <div class="content">
        <div class="pull-right flush-right">
                        <span class="action-button pull-right" data-placement="bottom" data-dropdown="#action-dropdown-more" data-toggle="tooltip" title="Más">
                <i class="icon-caret-down pull-right"></i>
                <span ><i class="icon-cog"></i></span>
            </span>
                            <a class="action-button pull-right" data-placement="bottom" data-toggle="tooltip" title="Editar" href="tickets.php?id=230522&a=edit"><i class="icon-edit"></i></a>
                        <span class="action-button pull-right" data-placement="bottom" data-dropdown="#action-dropdown-print" data-toggle="tooltip" title="Imprimir">
                <i class="icon-caret-down pull-right"></i>
                <a id="ticket-print" aria-label="Imprimir" href="tickets.php?id=230522&a=print"><i class="icon-print"></i></a>
            </span>
            <div id="action-dropdown-print" class="action-dropdown anchor-right">
              <ul>
                 <li title="PDF File"><a class="no-pjax" target="_blank" href="tickets.php?id=230522&a=print&notes=0&events=0"><i
                 class="icon-file-text-alt"></i> Asunto del Ticket</a>
                 <li title="PDF File"><a class="no-pjax" target="_blank" href="tickets.php?id=230522&a=print&notes=1&events=0"><i
                 class="icon-file-text-alt"></i> Asunto + Notas internas</a>
                 <li title="PDF File"><a class="no-pjax" target="_blank" href="tickets.php?id=230522&a=print&notes=1&events=1"><i
                 class="icon-file-text-alt"></i> Hilo + Notas Internas + Eventos</a>
                                  <li title="ZIP Archive"><a class="no-pjax" target="_blank" href="tickets.php?id=230522&a=zip&notes=1"><i
                 class="icon-folder-close-alt"></i> Hilo + Notas internas + Adjuntos</a>
                 <li title="ZIP Archive"><a class="no-pjax" target="_blank" href="tickets.php?id=230522&a=zip&notes=1&tasks=1"><i
                 class="icon-folder-close-alt"></i> Hilo + Notas internas + Adjuntos + Tareas</a>
                               </ul>
            </div>
                        <a class="action-button pull-right ticket-action" id="ticket-transfer" data-placement="bottom" data-toggle="tooltip" title="Transferir"
                data-redirect="tickets.php"
                href="#tickets/230522/transfer"><i class="icon-share"></i></a>
            
                        <span class="action-button pull-right"
                data-dropdown="#action-dropdown-assign"
                data-placement="bottom"
                data-toggle="tooltip"
                title=" Reasignar"
                >
                <i class="icon-caret-down pull-right"></i>
                <a class="ticket-action" id="ticket-assign"
                    data-redirect="tickets.php"
                    href="#tickets/230522/assign"><i class="icon-user"></i></a>
            </span>
            <div id="action-dropdown-assign" class="action-dropdown anchor-right">
              <ul>
                                 <li><a class="no-pjax ticket-action"
                    data-redirect="tickets.php?id=230522"
                    href="#tickets/230522/claim"><i
                    class="icon-chevron-sign-down"></i> Reclamar</a>
                                 <li><a class="no-pjax ticket-action"
                    data-redirect="tickets.php"
                    href="#tickets/230522/assign/agents"><i
                    class="icon-user"></i> Agente</a>
                 <li><a class="no-pjax ticket-action"
                    data-redirect="tickets.php"
                    href="#tickets/230522/assign/teams"><i
                    class="icon-group"></i> Equipo</a>
              </ul>
            </div>
                        <div id="action-dropdown-more" class="action-dropdown anchor-right">
              <ul>
                                    <li><a class="change-user" href="#tickets/230522/change-user"
                    onclick="javascript:
                        saveDraft();"
                    ><i class="icon-user"></i> Cambiar Propietario</a></li>
                                     <li><a href="#ajax.php/tickets/230522/merge" onclick="javascript:
                         $.dialog($(this).attr('href').substr(1), 201);
                         return false"
                         ><i class="icon-code-fork"></i> Unir tickets</a></li>
                                      <li><a href="#ajax.php/tickets/230522/link" onclick="javascript:
                         $.dialog($(this).attr('href').substr(1), 201);
                         return false"
                         ><i class="icon-link"></i> Enlazar tickets</a></li>
                                         <li><a class="confirm-action" id="ticket-overdue" href="#overdue"><i class="icon-bell"></i> Marcar como retrasado</a></li>
                                        <li><a href="#tickets/230522/mark/answered" class="ticket-action"
                            data-redirect="tickets.php?id=230522">
                            <i class="icon-circle-arrow-right"></i> Marcar como contestados</a></li>
                    
                                <li><a href="#tickets/230522/referrals" class="ticket-action"
                     data-redirect="tickets.php?id=230522" >
                       <i class="icon-exchange"></i> Administrar referidos</a></li>
                                                <li><a href="#ajax.php/tickets/230522/forms/manage" onclick="javascript:
                    $.dialog($(this).attr('href').substr(1), 201);
                    return false"
                    ><i class="icon-paste"></i> Gestionar formularios</a></li>
                                <li>

                    <a class="collaborators manage-collaborators"
                            href="#thread/230524/collaborators/1"><i class="icon-group"></i> Gestionar Colaboradores</a>                </li>
                

              </ul>
            </div>
                                <a href="#post-reply" class="post-response action-button"
                data-placement="bottom" data-toggle="tooltip"
                title="Publicar Respuesta"><i class="icon-mail-reply"></i></a>
                                <a href="#post-note" id="post-note" class="post-response action-button"
                data-placement="bottom" data-toggle="tooltip"
                title="publicar nota interna"><i class="icon-file-text"></i></a>
                
<span
    class="action-button"
    data-dropdown="#action-dropdown-statuses" data-placement="bottom" data-toggle="tooltip" title="Cambiar Estado">
    <i class="icon-caret-down pull-right"></i>
    <a class="tickets-action"
        aria-label="Cambiar Estado"
        href="#statuses"><i
        class="icon-flag"></i></a>
</span>
<div id="action-dropdown-statuses"
    class="action-dropdown anchor-right">
    <ul >
        <li>
            <a class="no-pjax ticket-action"
                href="#tickets/230522/status/close/3"
                data-redirect="tickets.php"                ><i class="icon-ok-circle"></i> Cerrado</a>
        </li>
        </ul>
</div>
           </div>
        <div class="flush-left">
             <h2><a href="tickets.php?id=230522"
             title="Actualizar"><i class="icon-refresh"></i>
             Ticket #230205</a>
            </h2>
        </div>
    </div>
  </div>
</div>
<div class="clear tixTitle has_bottom_border">
    <h3>
    DICTAMEN E INSCRIPCIÓN DEL PROYECTO DE TESIS    </h3>
</div>
<table class="ticket_info" cellspacing="0" cellpadding="0" width="940" border="0">
    <tr>
        <td width="50%">
            <table border="0" cellspacing="0" cellpadding="4" width="100%">
                <tr>
                    <th width="100">Estado:</th>
                                             <td>
                          <a class="tickets-action" data-dropdown="#action-dropdown-statuses" data-placement="bottom" data-toggle="tooltip" title="Cambiar Estado"
                              data-redirect="tickets.php?id=230522"
                              href="#statuses"
                              onclick="javascript:
                                  saveDraft();"
                              >
                              Open                          </a>
                        </td>
                                      </tr>
                <tr>
                    <th>Prioridad:</th>
                                                 <td>
                             <a class="inline-edit" data-placement="bottom" data-toggle="tooltip" title="Actualizar"
                                 href="#tickets/230522/field/22/edit">
                                 <span id="field_22">Normal</span>
                             </a>
                           </td>
                                      </tr>
                <tr>
                    <th>Departamento:</th>
                                          <td>
                          <a class="ticket-action" data-placement="bottom" data-toggle="tooltip" title="Transferir"
                            data-redirect="tickets.php?id=230522"
                            href="#tickets/230522/transfer"
                            onclick="javascript:
                                saveDraft();"
                            >Escuela de Posgrado                        </a>
                      </td>
                                    </tr>
                <tr>
                    <th>Creado en:</th>
                    <td>22/06/2026 03:27 p.m.</td>
                </tr>
            </table>
        </td>
        <td width="50%" style="vertical-align:top">
            <table border="0" cellspacing="0" cellpadding="4" width="100%">
                <tr>
                    <th width="100">Usuario:</th>
                    <td><a href="#tickets/230522/user"
                        onclick="javascript:
                            saveDraft();
                            $.userLookup('ajax.php/tickets/230522/user',
                                    function (user) {
                                        $('#user-'+user.id+'-name').text(user.name);
                                        $('#user-'+user.id+'-email').text(user.email);
                                        $('#user-'+user.id+'-phone').text(user.phone);
                                        $('select#emailreply option[value=1]').text(user.name+' <'+user.email+'>');
                                    });
                            return false;
                            "><i class="icon-user"></i> <span id="user-13331-name"
                            >ANDY FLORES CUCCHI</span></a>
                                                    <a href="tickets.php?status=open&amp;a=search&amp;uid=13331" title="Solicitudes relacionadas"
                            data-dropdown="#action-dropdown-stats">
                            (<b>6</b>)
                            </a>
                            <div id="action-dropdown-stats" class="action-dropdown anchor-right">
                                <ul>
                                    <li><a href="tickets.php?a=search&status=open&uid=13331"><i class="icon-folder-open-alt icon-fixed-width"></i> 2 Solicitudes abiertas</a></li><li><a href="tickets.php?a=search&status=closed&uid=13331"><i
                                                class="icon-folder-close-alt icon-fixed-width"></i> 4 Tickets cerrados</a></li>                                    <li><a href="tickets.php?a=search&uid=13331"><i class="icon-double-angle-right icon-fixed-width"></i> Todos las Solicitudes</a></li>
                                </ul>
                            </div>
                            <span><a class="manage-collaborators preview"
                                    href="#thread/230524/collaborators/1"><span id="t230524-recipients"><i class="icon-group"></i> ( Gestionar Colaboradores)</span></a></span>                    </td>
                </tr>
                <tr>
                    <th>Correo electrónico:</th>
                    <td>
                        <span id="user-13331-email">016102342A@uandina.edu.pe</span>
                    </td>
                </tr>
                <tr>
                  <th>Fuente:</th>
                  <td>
                                      <a class="inline-edit" data-placement="bottom" data-toggle="tooltip" title="Actualizar"
                        href="#tickets/230522/field/source/edit">
                        <span id="field_source">
                        Web</span>
                    </a>
                      &nbsp;&nbsp; <span class="faded">(190.81.173.211)</span>                 </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
<br>
<table class="ticket_info" cellspacing="0" cellpadding="0" width="940" border="0">
    <tr>
        <td width="50%">
            <table cellspacing="0" cellpadding="4" width="100%" border="0">
                                <tr>
                    <th width="100">Asignado a:</th>
                                        <td>
                        <a class="inline-edit" data-placement="bottom" data-toggle="tooltip" title="Actualizar"
                            href="#tickets/230522/assign">
                            <span id="field_assign">
                                <span class="faded">&mdash; No asignado &mdash;</span></span>
                        </a>
                    </td>
                                    </tr>
                                <tr>
                    <th>Plan SLA:</th>
                    <td>
                                              <a class="inline-edit" data-placement="bottom" data-toggle="tooltip" title="Actualizar"
                          href="#tickets/230522/field/sla/edit">
                          <span id="field_sla">SLA de 3 días</span>
                      </a>
                                          </td>
                </tr>
                                <tr>
                    <th>Fecha de Vencimiento:</th>
                                               <td>
                      <a class="inline-edit" data-placement="bottom" data-toggle="tooltip"
                          title="Actualizar"
                          href="#tickets/230522/field/duedate/edit">
                                                      <span id="field_duedate" >
                               09/07/2026 03:27 p.m.                           </span>
                      </a>
                           </td>
                                      </tr>
                            </table>
        </td>
        <td width="50%">
            <table cellspacing="0" cellpadding="4" width="100%" border="0">
                <tr>
                    <th width="100">Temas de ayuda:</th>
                                                   <td>
                        <a class="inline-edit" data-placement="bottom"
                            data-toggle="tooltip" title="Actualizar"
                            href="#tickets/230522/field/topic/edit">
                            <span id="field_topic">
                                1. Soy Estudiante                            </span>
                        </a>
                      </td>
                                        </tr>
                <tr>
                    <th nowrap>Último mensaje:</th>
                    <td>03/07/2026 10:36 a.m.</td>
                </tr>
                <tr>
                    <th nowrap>Última respuesta:</th>
                    <td>22/06/2026 03:29 p.m.</td>
                </tr>
            </table>
        </td>
    </tr>
</table>
<br>
    <table class="ticket_info custom-data" cellspacing="0" cellpadding="0" width="940" border="0">
    <thead>
        <th colspan="2">Detalles del Trámite / Solicitud</th>
    </thead>
    <tbody>
        <tr>
            <td width="200">Acepto los términos y condiciones:</td>
            <td id="inline-answer-52">
                              <a class="inline-edit" data-placement="bottom" data-toggle="tooltip" title="Actualizar"
                      href="#tickets/230522/field/52/edit">
                  <span id="field_52"  >Sí</span>              </a>
                        </td>
        </tr>
    </tbody>
    </table>
    <table class="ticket_info custom-data" cellspacing="0" cellpadding="0" width="940" border="0">
    <thead>
        <th colspan="2">Datos Estudiante</th>
    </thead>
    <tbody>
        <tr>
            <td width="200">Código de estudiante:</td>
            <td id="inline-answer-44">
                              <a class="inline-edit" data-placement="bottom" data-toggle="tooltip" title="Actualizar"
                      href="#tickets/230522/field/44/edit">
                  <span id="field_44"  >016102342A</span>              </a>
                        </td>
        </tr>
        <tr>
            <td width="200">Filial / Escuela Profesional / Posgrado:</td>
            <td id="inline-answer-45">
                              <a class="inline-edit" data-placement="bottom" data-toggle="tooltip" title="Actualizar"
                      href="#tickets/230522/field/45/edit">
                  <span id="field_45"  >Cusco / Administración de Negocios Internacionales</span>              </a>
                        </td>
        </tr>
    </tbody>
    </table>
<div class="clear"></div>

<ul  class="tabs clean threads" id="ticket_tabs" >
    <li class="active"><a id="ticket-thread-tab" href="#ticket_thread">Hilo de la Solicitud (6)</a></li>
    <li><a id="ticket-tasks-tab" href="#tasks"
            data-url="#tickets/230522/tasks">Tareas</a></li>
    
</ul>

<div id="ticket_tabs_container">
<div id="ticket_thread" class="tab_content">

<div id="ticketThread">
    <div id="thread-items" data-thread-id="230524">
    <div id="thread-entry-959426"><div class="thread-entry message avatar" style="position:relative;z-index:auto;">
    <span class="pull-right avatar">
<img  class="avatar" alt="Avatar" src="//www.gravatar.com/avatar/c1ef39e43a08ebe355f91ac8e7d33024?s=80&d=mm" />    </span>
    <div class="header">
        <div class="pull-right">
        <span class="muted-button pull-right" data-dropdown="#entry-action-more-959426">
            <i class="icon-caret-down"></i>
        </span>
        <div id="entry-action-more-959426" class="action-dropdown anchor-right">
            <ul class="title">
                <li>
                    <a class="no-pjax" href="#" onclick="javascript:
                    var url = 'ajax.php/tickets/230522/thread/959426/edit';
$.dialog(url, [201], function(xhr, resp) {
  var json = JSON.parse(resp);
  if (!json || !json.thread_id)
    return;
  $('#thread-entry-'+json.thread_id)
    .attr('id', 'thread-entry-' + json.new_id)
    .html(json.entry)
    .find('.thread-body')
    .delay(500)
    .effect('highlight');
}, {size:'large'});; return false;">
                    <i class="icon-pencil"></i> Editar</a></li>
                <li>
                    <a class="no-pjax" href="#" onclick="javascript:
                             window.location.href = 'tickets.php?a=open&tid=959426';; return false;">
                    <i class="icon-plus"></i> Crear Ticket</a></li>
                <li>
                    <a class="no-pjax" href="#" onclick="javascript:
                    var url = 'ajax.php/tickets/230522/thread/959426/create_task';
var redirect = $(this).data('redirect');
$.dialog(url, [201], function(xhr, resp) {
    if (!!redirect)
        $.pjax({url: redirect, container: '#pjax-container'});
    else
        $.pjax({url: 'tickets.php?id=230522#tasks', container: '#pjax-container'});
});; return false;">
                    <i class="icon-plus"></i> Crear Tarea</a></li>
            </ul>
        </div>
        <span class="textra light">
        </span>
        </div>
<b>ANDY FLORES CUCCHI</b> publicado <a name="entry-959426" href="#entry-959426"><time 
                datetime="2026-06-22T20:27:08+00:00" data-toggle="tooltip" title="lunes, 22 junio 2026 03:27 p.m.">22/06/2026 03:27 p.m.</time></a>        <span style="max-width:400px" class="faded title truncate">        </span>
    </div>
    <div class="thread-body no-pjax">
        <div><p>Buenas Tardes </p> <p>Su amable apoyo:</p><h1><strong>DICTAMEN E INSCRIPCIÓN DEL PROYECTO DE TESIS</strong></h1></div>
        <div class="clear"></div>
    <div class="attachments">        <span class="attachment-info">
        <i class="icon-paperclip icon-flip-horizontal"></i>
        <a class="no-pjax truncate filename" href="/file.php?key=mt1cj5as3phveg6lxbz0j_mxjelqjvai&expires=1783123200&signature=fafb2e0cbbcd952c100838b0de14d41059bf2d0e&id=732119" download="CARTA DE CONFORMIDAD ANDY FLORES CUCCHI.pdf"
            target="_blank">CARTA DE CONFORMIDAD ANDY FLORES CUCCHI.pdf</a><small class="filesize faded">198.8 kb</small>        </span>
        <span class="attachment-info">
        <i class="icon-paperclip icon-flip-horizontal"></i>
        <a class="no-pjax truncate filename" href="/file.php?key=toqjj4atleikemdlsrp8dl8jo73uhyzo&expires=1783123200&signature=5598fa7e3df917eb56b447c7492c18076a6aa97c&id=732120" download="PROYECTO DE TESIS  11.06.26 (2).pdf"
            target="_blank">PROYECTO DE TESIS  11.06.26 (2).pdf</a><small class="filesize faded">0.9 mb</small>        </span>
        <span class="attachment-info">
        <i class="icon-paperclip icon-flip-horizontal"></i>
        <a class="no-pjax truncate filename" href="/file.php?key=wgoyd2ldcxgnsilifkjck7ou9eqr6suq&expires=1783123200&signature=2a60ce180c091a7430e4e1e2edf10dc7723b6cd3&id=732121" download="PROYECTO DE TESIS  11.06.26 (2).docx"
            target="_blank">PROYECTO DE TESIS  11.06.26 (2).docx</a><small class="filesize faded">1.7 mb</small>        </span>
</div>    </div>
</div>
</div><div class="thread-event action">
        <span class="type-icon">
          <i class="faded icon-magic"></i>
        </span>
        <span class="faded description">
            Creado por <b><img  class="avatar" alt="Avatar" src="//www.gravatar.com/avatar/c1ef39e43a08ebe355f91ac8e7d33024?s=80&d=mm" />ANDY FLORES CUCCHI</b><time  datetime="2026-06-22T20:27:08+00:00"
                            data-toggle="tooltip" title="lunes, 22 junio 2026 03:27 p.m.">22/06/2026 03:27 p.m.</time>        </span>
</div>
<div class="thread-event ">
        <span class="type-icon">
          <i class="faded icon-hand-right"></i>
        </span>
        <span class="faded description">
            <b>Filtros de Tickets</b> asignó esta a <strong></strong> <time  datetime="2026-06-22T20:27:11+00:00"
                            data-toggle="tooltip" title="lunes, 22 junio 2026 03:27 p.m.">22/06/2026 03:27 p.m.</time>        </span>
</div>
<div id="thread-entry-959434"><div class="thread-entry response avatar" style="position:relative;z-index:auto;">
    <span class="pull-left avatar">
<img  class="avatar" alt="Avatar" src="//www.gravatar.com/avatar/bda6b211475f83ccae51734d564e915c?s=80&d=mm" />    </span>
    <div class="header">
        <div class="pull-right">
        <span class="muted-button pull-right" data-dropdown="#entry-action-more-959434">
            <i class="icon-caret-down"></i>
        </span>
        <div id="entry-action-more-959434" class="action-dropdown anchor-right">
            <ul class="title">
                <li>
                    <a class="no-pjax" href="#" onclick="javascript:
                    $.dialog('ajax.php/tickets/230522/thread/959434/emailrecipients');; return false;">
                    <i class="icon-group"></i> View Email Recipients</a></li>
                <li>
                    <a class="no-pjax" href="#" onclick="javascript:
                    var url = 'ajax.php/tickets/230522/thread/959434/edit_resend';
$.dialog(url, [201], function(xhr, resp) {
  var json = JSON.parse(resp);
  if (!json || !json.thread_id)
    return;
  $('#thread-entry-'+json.thread_id)
    .attr('id', 'thread-entry-' + json.new_id)
    .html(json.entry)
    .find('.thread-body')
    .delay(500)
    .effect('highlight');
}, {size:'large'});; return false;">
                    <i class="icon-reply-all"></i> Edit and Resend</a></li>
                <li>
                    <a class="no-pjax" href="#" onclick="javascript:
                             window.location.href = 'tickets.php?a=open&tid=959434';; return false;">
                    <i class="icon-plus"></i> Crear Ticket</a></li>
                <li>
                    <a class="no-pjax" href="#" onclick="javascript:
                    var url = 'ajax.php/tickets/230522/thread/959434/create_task';
var redirect = $(this).data('redirect');
$.dialog(url, [201], function(xhr, resp) {
    if (!!redirect)
        $.pjax({url: redirect, container: '#pjax-container'});
    else
        $.pjax({url: 'tickets.php?id=230522#tasks', container: '#pjax-container'});
});; return false;">
                    <i class="icon-plus"></i> Crear Tarea</a></li>
            </ul>
        </div>
        <span class="textra light">
            <span class="label label-bare"><i class="icon-user"></i></span>
        </span>
        </div>
<b>Julio Cesar Zarate Tapia</b> publicado <a name="entry-959434" href="#entry-959434"><time 
                datetime="2026-06-22T20:29:09+00:00" data-toggle="tooltip" title="lunes, 22 junio 2026 03:29 p.m.">22/06/2026 03:29 p.m.</time></a>        <span style="max-width:400px" class="faded title truncate">        </span>
    </div>
    <div class="thread-body no-pjax">
        <div><p>Su trámite ha sido registrado y derivado con los siguientes datos:</p> <table style="border:1px solid black"><tbody><tr><td style="border:1px solid black"><p><strong>EXPEDIENTE</strong></p></td><td style="border:1px solid black"><strong>DERIVADO A</strong></td></tr><tr><td style="border:1px solid black">Nro:22052</td><td style="border:1px solid black">Dependencia: Escuela de Posgrado UAC.</td></tr></tbody></table> <p><em>*Para realizar el seguimiento a tu trámite <strong>sólo responde desde tu correo electrónico a este mensaje</strong> o <a href="https://mesadepartes.uandina.edu.pe/view.php?auth=o1xcm0aaad0qqbqaanfnIK4xDthavQ%3D%3D">haz clic aquí</a>. Asimismo, cualquier duda, consulta y/o levantamiento de observaciones la debe realizar respondiendo al presente correo.</em></p> <p>Atentamente.</p></div>
        <div class="clear"></div>
    </div>
</div>
</div><div class="thread-event action">
        <span class="type-icon">
          <i class="faded icon-share-alt"></i>
        </span>
        <span class="faded description">
            <b><img  class="avatar" alt="Avatar" src="//www.gravatar.com/avatar/bda6b211475f83ccae51734d564e915c?s=80&d=mm" />Julio Cesar Zarate Tapia</b> transfirió esta a <strong>Escuela de Posgrado</strong><time  datetime="2026-06-22T20:29:19+00:00"
                            data-toggle="tooltip" title="lunes, 22 junio 2026 03:29 p.m.">22/06/2026 03:29 p.m.</time>        </span>
</div>
<div id="thread-entry-961563"><div class="thread-entry message avatar" style="position:relative;z-index:auto;">
    <span class="pull-right avatar">
<img  class="avatar" alt="Avatar" src="//www.gravatar.com/avatar/c1ef39e43a08ebe355f91ac8e7d33024?s=80&d=mm" />    </span>
    <div class="header">
        <div class="pull-right">
        <span class="muted-button pull-right" data-dropdown="#entry-action-more-961563">
            <i class="icon-caret-down"></i>
        </span>
        <div id="entry-action-more-961563" class="action-dropdown anchor-right">
            <ul class="title">
                <li>
                    <a class="no-pjax" href="#" onclick="javascript:
                    var url = 'ajax.php/tickets/230522/thread/961563/edit';
$.dialog(url, [201], function(xhr, resp) {
  var json = JSON.parse(resp);
  if (!json || !json.thread_id)
    return;
  $('#thread-entry-'+json.thread_id)
    .attr('id', 'thread-entry-' + json.new_id)
    .html(json.entry)
    .find('.thread-body')
    .delay(500)
    .effect('highlight');
}, {size:'large'});; return false;">
                    <i class="icon-pencil"></i> Editar</a></li>
                <li>
                    <a class="no-pjax" href="#" onclick="javascript:
                             window.location.href = 'tickets.php?a=open&tid=961563';; return false;">
                    <i class="icon-plus"></i> Crear Ticket</a></li>
                <li>
                    <a class="no-pjax" href="#" onclick="javascript:
                    var url = 'ajax.php/tickets/230522/thread/961563/create_task';
var redirect = $(this).data('redirect');
$.dialog(url, [201], function(xhr, resp) {
    if (!!redirect)
        $.pjax({url: redirect, container: '#pjax-container'});
    else
        $.pjax({url: 'tickets.php?id=230522#tasks', container: '#pjax-container'});
});; return false;">
                    <i class="icon-plus"></i> Crear Tarea</a></li>
            </ul>
        </div>
        <span class="textra light">
        </span>
        </div>
<b>ANDY FLORES CUCCHI</b> publicado <a name="entry-961563" href="#entry-961563"><time 
                datetime="2026-06-25T19:18:39+00:00" data-toggle="tooltip" title="jueves, 25 junio 2026 02:18 p.m.">25/06/2026 02:18 p.m.</time></a>        <span style="max-width:400px" class="faded title truncate">        </span>
    </div>
    <div class="thread-body no-pjax">
        <div><p>Buenas Tardes </p> <p>Su amable apoyo:</p> <h1><strong>DICTAMEN E INSCRIPCIÓN DEL PROYECTO DE TESIS</strong></h1></div>
        <div class="clear"></div>
    </div>
</div>
</div><div id="thread-entry-962330"><div class="thread-entry message avatar" style="position:relative;z-index:auto;">
    <span class="pull-right avatar">
<img  class="avatar" alt="Avatar" src="//www.gravatar.com/avatar/c1ef39e43a08ebe355f91ac8e7d33024?s=80&d=mm" />    </span>
    <div class="header">
        <div class="pull-right">
        <span class="muted-button pull-right" data-dropdown="#entry-action-more-962330">
            <i class="icon-caret-down"></i>
        </span>
        <div id="entry-action-more-962330" class="action-dropdown anchor-right">
            <ul class="title">
                <li>
                    <a class="no-pjax" href="#" onclick="javascript:
                    var url = 'ajax.php/tickets/230522/thread/962330/edit';
$.dialog(url, [201], function(xhr, resp) {
  var json = JSON.parse(resp);
  if (!json || !json.thread_id)
    return;
  $('#thread-entry-'+json.thread_id)
    .attr('id', 'thread-entry-' + json.new_id)
    .html(json.entry)
    .find('.thread-body')
    .delay(500)
    .effect('highlight');
}, {size:'large'});; return false;">
                    <i class="icon-pencil"></i> Editar</a></li>
                <li>
                    <a class="no-pjax" href="#" onclick="javascript:
                             window.location.href = 'tickets.php?a=open&tid=962330';; return false;">
                    <i class="icon-plus"></i> Crear Ticket</a></li>
                <li>
                    <a class="no-pjax" href="#" onclick="javascript:
                    var url = 'ajax.php/tickets/230522/thread/962330/create_task';
var redirect = $(this).data('redirect');
$.dialog(url, [201], function(xhr, resp) {
    if (!!redirect)
        $.pjax({url: redirect, container: '#pjax-container'});
    else
        $.pjax({url: 'tickets.php?id=230522#tasks', container: '#pjax-container'});
});; return false;">
                    <i class="icon-plus"></i> Crear Tarea</a></li>
            </ul>
        </div>
        <span class="textra light">
        </span>
        </div>
<b>ANDY FLORES CUCCHI</b> publicado <a name="entry-962330" href="#entry-962330"><time 
                datetime="2026-06-26T15:58:06+00:00" data-toggle="tooltip" title="viernes, 26 junio 2026 10:58 a.m.">26/06/2026 10:58 a.m.</time></a>        <span style="max-width:400px" class="faded title truncate">        </span>
    </div>
    <div class="thread-body no-pjax">
        <div><p>Buenas Tardes</p> <p>Su amable apoyo:</p> <h1><strong>DICTAMEN E INSCRIPCIÓN DEL PROYECTO DE TESIS</strong></h1></div>
        <div class="clear"></div>
    </div>
</div>
</div><div id="thread-entry-964037"><div class="thread-entry message avatar" style="position:relative;z-index:auto;">
    <span class="pull-right avatar">
<img  class="avatar" alt="Avatar" src="//www.gravatar.com/avatar/c1ef39e43a08ebe355f91ac8e7d33024?s=80&d=mm" />    </span>
    <div class="header">
        <div class="pull-right">
        <span class="muted-button pull-right" data-dropdown="#entry-action-more-964037">
            <i class="icon-caret-down"></i>
        </span>
        <div id="entry-action-more-964037" class="action-dropdown anchor-right">
            <ul class="title">
                <li>
                    <a class="no-pjax" href="#" onclick="javascript:
                    var url = 'ajax.php/tickets/230522/thread/964037/edit';
$.dialog(url, [201], function(xhr, resp) {
  var json = JSON.parse(resp);
  if (!json || !json.thread_id)
    return;
  $('#thread-entry-'+json.thread_id)
    .attr('id', 'thread-entry-' + json.new_id)
    .html(json.entry)
    .find('.thread-body')
    .delay(500)
    .effect('highlight');
}, {size:'large'});; return false;">
                    <i class="icon-pencil"></i> Editar</a></li>
                <li>
                    <a class="no-pjax" href="#" onclick="javascript:
                             window.location.href = 'tickets.php?a=open&tid=964037';; return false;">
                    <i class="icon-plus"></i> Crear Ticket</a></li>
                <li>
                    <a class="no-pjax" href="#" onclick="javascript:
                    var url = 'ajax.php/tickets/230522/thread/964037/create_task';
var redirect = $(this).data('redirect');
$.dialog(url, [201], function(xhr, resp) {
    if (!!redirect)
        $.pjax({url: redirect, container: '#pjax-container'});
    else
        $.pjax({url: 'tickets.php?id=230522#tasks', container: '#pjax-container'});
});; return false;">
                    <i class="icon-plus"></i> Crear Tarea</a></li>
            </ul>
        </div>
        <span class="textra light">
        </span>
        </div>
<b>ANDY FLORES CUCCHI</b> publicado <a name="entry-964037" href="#entry-964037"><time 
                datetime="2026-06-30T21:01:50+00:00" data-toggle="tooltip" title="martes, 30 junio 2026 04:01 p.m.">30/06/2026 04:01 p.m.</time></a>        <span style="max-width:400px" class="faded title truncate">        </span>
    </div>
    <div class="thread-body no-pjax">
        <div><p>Buenas Tardes</p> <p>Su amable apoyo:</p> <h1><strong>DICTAMEN E INSCRIPCIÓN DEL PROYECTO DE TESIS</strong></h1></div>
        <div class="clear"></div>
    </div>
</div>
</div><div id="thread-entry-965219"><div class="thread-entry message avatar" style="position:relative;z-index:auto;">
    <span class="pull-right avatar">
<img  class="avatar" alt="Avatar" src="//www.gravatar.com/avatar/c1ef39e43a08ebe355f91ac8e7d33024?s=80&d=mm" />    </span>
    <div class="header">
        <div class="pull-right">
        <span class="muted-button pull-right" data-dropdown="#entry-action-more-965219">
            <i class="icon-caret-down"></i>
        </span>
        <div id="entry-action-more-965219" class="action-dropdown anchor-right">
            <ul class="title">
                <li>
                    <a class="no-pjax" href="#" onclick="javascript:
                    var url = 'ajax.php/tickets/230522/thread/965219/edit';
$.dialog(url, [201], function(xhr, resp) {
  var json = JSON.parse(resp);
  if (!json || !json.thread_id)
    return;
  $('#thread-entry-'+json.thread_id)
    .attr('id', 'thread-entry-' + json.new_id)
    .html(json.entry)
    .find('.thread-body')
    .delay(500)
    .effect('highlight');
}, {size:'large'});; return false;">
                    <i class="icon-pencil"></i> Editar</a></li>
                <li>
                    <a class="no-pjax" href="#" onclick="javascript:
                             window.location.href = 'tickets.php?a=open&tid=965219';; return false;">
                    <i class="icon-plus"></i> Crear Ticket</a></li>
                <li>
                    <a class="no-pjax" href="#" onclick="javascript:
                    var url = 'ajax.php/tickets/230522/thread/965219/create_task';
var redirect = $(this).data('redirect');
$.dialog(url, [201], function(xhr, resp) {
    if (!!redirect)
        $.pjax({url: redirect, container: '#pjax-container'});
    else
        $.pjax({url: 'tickets.php?id=230522#tasks', container: '#pjax-container'});
});; return false;">
                    <i class="icon-plus"></i> Crear Tarea</a></li>
            </ul>
        </div>
        <span class="textra light">
        </span>
        </div>
<b>ANDY FLORES CUCCHI</b> publicado <a name="entry-965219" href="#entry-965219"><time 
                datetime="2026-07-03T15:36:18+00:00" data-toggle="tooltip" title="viernes, 3 julio 2026 10:36 a.m.">03/07/2026 10:36 a.m.</time></a>        <span style="max-width:400px" class="faded title truncate">        </span>
    </div>
    <div class="thread-body no-pjax">
        <div><p>Buenos días </p> <p>Su amable apoyo no tengo respuesta.</p> <p><br /></p> <p>Atte.</p></div>
        <div class="clear"></div>
    </div>
</div>
</div>    </div>
</div>
<script type="text/javascript">
    $(function() {
        var container = 'ticketThread';

        // Set inline image urls.
                $('#'+container).data('imageUrls', []);
        // Trigger thread processing.
        if ($.thread)
            $.thread.onLoad(container,
                    {autoScroll: true});
    });
</script>
<div class="clear"></div>

<div class="sticky bar stop actions" id="response_options"
>
    <ul class="tabs" id="response-tabs">
                <li class="active "><a
            href="#reply" id="post-reply-tab">Publicar Respuesta</a></li>
                <li><a href="#note"             id="post-note-tab">publicar nota interna</a></li>
            </ul>
        <form id="reply" class="tab_content spellcheck exclusive save"
        data-lock-object-id="ticket/230522"
        data-lock-id=""
        action="tickets.php?id=230522#reply" name="reply" method="post" enctype="multipart/form-data">
        <input type="hidden" name="__CSRFToken__" value="9d44856b3c4571060e82017964a25cbbe4c635fb" />        <input type="hidden" name="id" value="230522">
        <input type="hidden" name="msgId" value="">
        <input type="hidden" name="a" value="reply">
        <input type="hidden" name="lockCode" value="">
        <table style="width:100%" border="0" cellspacing="0" cellpadding="3">
                       <tbody id="to_sec">
           <tr>
               <td width="120">
                   <label><strong>De:</strong></label>
               </td>
               <td>
                   <select id="from_email_id" name="from_email_id">
                     <option value="1" selected="selected">Mesa de Partes Virtual UAndina &lt;mesadepartesvirtual@uandina.edu.pe&gt;</option>                   </select>
               </td>
           </tr>
            </tbody>
            <tbody id="recipients">
             <tr id="user-row">
                <td width="120">
                    <label><strong>Destinatarios:</strong></label>
                </td>
                <td><a href="#tickets/230522/user"
                    onclick="javascript:
                        $.userLookup('ajax.php/tickets/230522/user',
                                function (user) {
                                    window.location = 'tickets.php?id='                                });
                        return false;
                        "><span >&quot;ANDY FLORES CUCCHI&quot; &lt;016102342A@uandina.edu.pe&gt;</span></a>
                </td>
              </tr>
               <tr><td>&nbsp;</td>
                   <td>
                   <div style="margin-bottom:2px;">
                    <span"><a id="show_ccs">
                                 <i id="arrow-icon" class="icon-caret-right"></i>&nbsp;Colaboradores </a>
                                 &nbsp;
                                 <a class="manage-collaborators
                                 collaborators preview noclick hidden"
                                  href="#thread/230524/collaborators/1">
                                 <span id="t230524-recipients"> Gestionar Colaboradores</span></a></span></a></span>                   </div>
                   <div id="ccs" class="hidden">
                     <div>
                        <span style="margin: 10px 5px 1px 0;" class="faded pull-left">Seleccionar o añadir nuevos colaboradores&nbsp;</span>
                                                <span class="action-button pull-left" style="margin: 2px  0 5px 20px;"
                            data-dropdown="#action-dropdown-collaborators"
                            data-placement="bottom"
                            data-toggle="tooltip"
                            title="Gestionar colaboradores"
                            >
                            <i class="icon-caret-down pull-right"></i>
                            <a class="ticket-action" id="collabs-button"
                                data-redirect="tickets.php?id=230522"
                                href="#thread/230524/collaborators/1">
                                <i class="icon-group"></i></a>
                         </span>
                                                  <span class="error">&nbsp;&nbsp;</span>
                        </div>
                                                <div id="action-dropdown-collaborators" class="action-dropdown anchor-right">
                          <ul>
                             <li><a class="manage-collaborators"
                                href="#thread/230524/add-collaborator/addcc"><i
                                class="icon-plus"></i> Añadir Nuevo</a>
                             <li><a class="manage-collaborators"
                                href="#thread/230524/collaborators/1"><i
                                class="icon-cog"></i> Gestionar colaboradores</a>
                          </ul>
                        </div>
                                             <div class="clear">
                      <select id="collabselection" name="ccs[]" multiple="multiple"
                          data-placeholder="Seleccionar colaboradores activos">
                                                </select>
                     </div>
                 </div>
                 </td>
             </tr>
             <tr>
                <td width="120">
                    <label>Responder A:</label>
                </td>
                <td>
                                        <select id="reply-to" name="reply-to">
                        <option value="all" selected="selected">Todos los Destinatarios activos</option><option value="user" >Propietario del Ticket (016102342A@uandina.edu.pe)</option><option value="none" >&mdash; No contestar al Email  &mdash;</option>                    </select>
                    <i class="help-tip icon-question-sign" href="#reply_types"></i>
                </td>
             </tr>
            </tbody>
            <tbody id="resp_sec">
            <tr><td colspan="2">&nbsp;</td></tr>
            <tr>
                <td width="120" style="vertical-align:top">
                    <label><strong>Respuesta:</strong></label>
                </td>
                <td>
                                  <div>
                    <select id="cannedResp" name="cannedResp">
                        <option value="0" selected="selected">Seleccione una respuesta predefinida</option>
                        <option value='original'>Mensaje original</option>
                        <option value='lastmessage'>Último mensaje</option>
                        <option value="0" disabled="disabled">
                                ------------- Respuestas predefinidas ------------- </option><option value="40">55% SITUAC</option><option value="39">55% SUDUAC</option><option value="26">ACCIONES DE SALUD</option><option value="28">ANVERSO</option><option value="27">ASIGNACION FAMILIAR</option><option value="34">CONSTANCIA DE PRACTICAS</option><option value="22">CONSTANCIA DE TRABAJO</option><option value="41">ENVIO DESARROLLO HUMANO</option><option value="21">ESCALAFON</option><option value="30">INFORME PRACTICANTE</option><option value="24">MAESTRIA Y DOCTORADO</option><option value="42">NECESIDAD DE SERVICIO</option><option value="35">PAGO POR CONSTANCIAS</option><option value="36">PAGO POR COPIA DE LEGAJO PERSONAL</option><option value="29">PATERNIDAD</option><option value="31">QUINQUENIO SITUAC</option><option value="25">REGULARIZAR CITT</option><option value="23">REMUNERACIONES</option><option value="37">SOLICITAR DOCUMENTOS 15%</option><option value="38">TESORERIA DESCUENTO 15%</option><option value="32">TIEMPO DE SERVICIO SITUAC</option>                    </select>
                    </div>
                    </td></tr>
                    <tr><td colspan="2">
                                    <input type="hidden" name="draft_id" value=""/>
                    <br/>
                    <textarea name="response" id="response" cols="50"
                        data-signature-field="signature" data-dept-id="63"
                        data-signature=""
                        placeholder="Empezar escribiendo su respuesta aquí. Usa respuestas predefinidas del menú desplegable de arriba"
                        rows="9" wrap="soft"
                        class="richtext draft draft-delete fullscreen" data-draft-namespace="ticket.response" data-draft-object-id="230522" data-draft-original=""></textarea>
                <div id="reply_form_attachments" class="attachments">
                <div id="e3661a4e88872697de8083" class="filedrop"><div class="files"></div>
            <div class="dropzone"><i class="icon-upload"></i>
            Soltar archivos aquí o <a href="#" class="manual"> elegirlos </a>        <input type="file" multiple="multiple"
            id="file-e3661a4e88872697de8083" style="display:none;"
            accept=""/>
        </div></div>
        <script type="text/javascript">
        $(function(){$('#e3661a4e88872697de8083 .dropzone').filedropbox({
          url: 'ajax.php/form/upload/attach',
          link: $('#e3661a4e88872697de8083').find('a.manual'),
          paramname: 'upload[]',
          fallback_id: 'file-e3661a4e88872697de8083',
          allowedfileextensions: [],
          allowedfiletypes: [],
          maxfiles: 20,
          maxfilesize: 32,
          name: 'c1c659b738162a[]',
          files: []        });});
        </script>
                </div>
                </td>
            </tr>
            <tr>
                <td width="120">
                    <label for="signature" class="left">Firma:</label>
                </td>
                <td>
                                        <label><input type="radio" name="signature" value="none" checked="checked"> Ninguno</label>
                                        <label><input type="radio" name="signature" value="mine"
                        > Mi firma</label>
                                                        </td>
            </tr>
            <tr>
                <td width="120" style="vertical-align:top">
                    <label><strong>Estado de la solicitud:</strong></label>
                </td>
                <td>
                                        <select name="reply_status_id">
                    <option value="1" selected="selected">Abiertos (actual)</option><option value="3" >Cerrado</option>                    </select>
                </td>
            </tr>
         </tbody>
        </table>
        <p  style="text-align:center;">
            <input class="save pending" type="submit" value="Publicar Respuesta">
            <input class="" type="reset" value="Restablecer">
        </p>
    </form>
        <form id="note" class="hidden tab_content spellcheck exclusive save"
        data-lock-object-id="ticket/230522"
        data-lock-id=""
        action="tickets.php?id=230522#note"
        name="note" method="post" enctype="multipart/form-data">
        <input type="hidden" name="__CSRFToken__" value="9d44856b3c4571060e82017964a25cbbe4c635fb" />        <input type="hidden" name="id" value="230522">
        <input type="hidden" name="locktime" value="1800">
        <input type="hidden" name="a" value="postnote">
        <input type="hidden" name="lockCode" value="">
        <table width="100%" border="0" cellspacing="0" cellpadding="3">
                        <tr>
                <td width="120" style="vertical-align:top">
                    <label><strong>Notas internas:</strong><span class='error'>&nbsp;*</span></label>
                </td>
                <td>
                    <div>
                        <div class="faded" style="padding-left:0.15em">Título de la nota - sumario de la nota (opcional)</div>
                        <input type="text" name="title" id="title" size="60" value="" >
                        <br/>
                        <span class="error">&nbsp;</span>
                    </div>
                </td></tr>
                <tr><td colspan="2">
                    <div class="error"></div>
                    <textarea name="note" id="internal_note" cols="80"
                        placeholder="Detalles de la nota"
                        rows="9" wrap="soft"
                        class="richtext draft draft-delete fullscreen" data-draft-namespace="ticket.note" data-draft-object-id="230522" data-draft-original=""></textarea>
                <div class="attachments">
                <div id="cf685dfd212e5a178dbd81" class="filedrop"><div class="files"></div>
            <div class="dropzone"><i class="icon-upload"></i>
            Soltar archivos aquí o <a href="#" class="manual"> elegirlos </a>        <input type="file" multiple="multiple"
            id="file-cf685dfd212e5a178dbd81" style="display:none;"
            accept=""/>
        </div></div>
        <script type="text/javascript">
        $(function(){$('#cf685dfd212e5a178dbd81 .dropzone').filedropbox({
          url: 'ajax.php/form/upload/attach',
          link: $('#cf685dfd212e5a178dbd81').find('a.manual'),
          paramname: 'upload[]',
          fallback_id: 'file-cf685dfd212e5a178dbd81',
          allowedfileextensions: [],
          allowedfiletypes: [],
          maxfiles: 20,
          maxfilesize: 32,
          name: '4f142204d8c460[]',
          files: []        });});
        </script>
                </div>
                </td>
            </tr>
            <tr><td colspan="2">&nbsp;</td></tr>
            <tr>
                <td width="120">
                    <label>Estado de la solicitud:</label>
                </td>
                <td>
                    <div class="faded"></div>
                    <select name="note_status_id">
                        <option value="1" selected="selected">Abiertos (actual)</option><option value="3" >Cerrado</option>                    </select>
                    &nbsp;<span class='error'>*&nbsp;</span>
                </td>
            </tr>
        </table>

       <p style="text-align:center;">
           <input class="save pending" type="submit" value="Publicar nota">
           <input class="" type="reset" value="Restablecer">
       </p>
   </form>
    </div>
 </div>
</div>
<div style="display:none;" class="dialog" id="print-options">
    <h3>Opciones de impresión de Solicitud</h3>
    <a class="close" href=""><i class="icon-remove-circle"></i></a>
    <hr/>
    <form action="tickets.php?id=230522"
        method="post" id="print-form" name="print-form" target="_blank">
        <input type="hidden" name="__CSRFToken__" value="9d44856b3c4571060e82017964a25cbbe4c635fb" />        <input type="hidden" name="a" value="print">
        <input type="hidden" name="id" value="230522">
        <fieldset class="notes">
            <label class="fixed-size" for="notes">Imprimir notas:</label>
            <label class="inline checkbox">
            <input type="checkbox" id="notes" name="notes" value="1"> Imprimir notas y comentarios <b>internos</b>            </label>
        </fieldset>
        <fieldset class="events">
            <label class="fixed-size" for="events">Imprimir Eventos:</label>
            <label class="inline checkbox">
            <input type="checkbox" id="events" name="events" value="1"> Imprimir Eventos del Hilo            </label>
        </fieldset>
        <fieldset>
            <label class="fixed-size" for="psize">Tamaño del papel:</label>
            <select id="psize" name="psize">
                <option value="">&mdash; Seleccione el tamaño del papel de impresión &mdash;</option>
                <option value="Letter" selected="selected">Carta</option><option value="Legal" >Oficio</option><option value="A4" >A4</option><option value="A3" >A3</option>            </select>
        </fieldset>
        <hr style="margin-top:3em"/>
        <p class="full-width">
            <span class="buttons pull-left">
                <input type="reset" value="Restablecer">
                <input type="button" value="Cancelar" class="close">
            </span>
            <span class="buttons pull-right">
                <input type="submit" value="Imprimir">
            </span>
         </p>
    </form>
    <div class="clear"></div>
</div>
<div style="display:none;" class="dialog" id="confirm-action">
    <h3>Por favor confirme</h3>
    <a class="close" href=""><i class="icon-remove-circle"></i></a>
    <hr/>
    <p class="confirm-action" style="display:none;" id="claim-confirm">
        ¿Está seguro de que desea <b> reclamar </b> (auto-asignarse) este ticket?    </p>
    <p class="confirm-action" style="display:none;" id="answered-confirm">
        ¿Está seguro que desea marcar el Ticket como <b>contestado</b>?    </p>
    <p class="confirm-action" style="display:none;" id="unanswered-confirm">
        ¿Está seguro que desea marcar el Ticket como <b>no contestado</b>?    </p>
    <p class="confirm-action" style="display:none;" id="overdue-confirm">
        ¿Está seguro que desea marcar el Ticket como <font color="red"> <b>atrasado</b></font>?    </p>
    <p class="confirm-action" style="display:none;" id="banemail-confirm">
        ¿Seguro que quieres <b>prohibir</b> 016102342A@uandina.edu.pe? <br><br>
        Nuevos Tickets procedentes de direcciones de correo electrónico serán automáticamente rechazados.    </p>
    <p class="confirm-action" style="display:none;" id="unbanemail-confirm">
        ¿Está seguro que desea <b>eliminar</b> 016102342A@uandina.edu.pe de la lista de prohibidos?    </p>
    <p class="confirm-action" style="display:none;" id="release-confirm">
        ¿Estás seguro de que desea <b>desasignar </b> el Ticket de <b> </b>?    </p>
    <p class="confirm-action" style="display:none;" id="changeuser-confirm">
        <span id="msg_warning" style="display:block;vertical-align:top">
        <b>ANDY FLORES CUCCHI</b> &lt;016102342A@uandina.edu.pe&gt; will no longer have access to the ticket        </span>
        ¿Está seguro de querer <b>cambiar</b> al dueño del ticket a <b><span id="newuser">this guy</span></b>?    </p>
    <p class="confirm-action" style="display:none;" id="delete-confirm">
        <font color="red"><strong>¿Está seguro que desea ELIMINAR este ticket?</strong></font>
        <br><br>Los elementos eliminados NO se pueden recuperar, incluyendo cualquier adjunto asociado.    </p>
    <div>Por favor confirme para continuar.</div>
    <form action="tickets.php?id=230522" method="post" id="confirm-form" name="confirm-form">
        <input type="hidden" name="__CSRFToken__" value="9d44856b3c4571060e82017964a25cbbe4c635fb" />        <input type="hidden" name="id" value="230522">
        <input type="hidden" name="a" value="process">
        <input type="hidden" name="do" id="action" value="">
        <hr style="margin-top:1em"/>
        <p class="full-width">
            <span class="buttons pull-left">
                <input type="button" value="Cancelar" class="close">
            </span>
            <span class="buttons pull-right">
                <input type="submit" value="Aceptar">
            </span>
         </p>
    </form>
    <div class="clear"></div>
</div>
<script type="text/javascript">
$(function() {
    $(document).on('click', 'a.change-user', function(e) {
        e.preventDefault();
        var tid = 13331;
        var cid = 13331;
        var url = 'ajax.php/'+$(this).attr('href').substr(1);
        $.userLookup(url, function(user) {
            if(cid!=user.id
                    && $('.dialog#confirm-action #changeuser-confirm').length) {
                $('#newuser').html(user.name +' &lt;'+user.email+'&gt;');
                $('.dialog#confirm-action #action').val('changeuser');
                $('#confirm-form').append('<input type=hidden name=user_id value='+user.id+' />');
                $('#overlay').show();
                $('.dialog#confirm-action .confirm-action').hide();
                $('.dialog#confirm-action p#changeuser-confirm')
                .show()
                .parent('div').show().trigger('click');
            }
        });
    });

    $(document).on('click', 'a.manage-collaborators', function(e) {
        e.preventDefault();
        var url = 'ajax.php/'+$(this).attr('href').substr(1);
        $.dialog(url, 201, function (xhr) {
           var resp = $.parseJSON(xhr.responseText);
           if (resp.user && !resp.users)
              resp.users.push(resp.user);
            // TODO: Process resp.users
           $('.tip_box').remove();
        }, {
            onshow: function() { $('#user-search').focus(); }
        });
        return false;
     });

    // Post Reply or Note action buttons.
    $('a.post-response').click(function (e) {
        var $r = $('ul.tabs > li > a'+$(this).attr('href')+'-tab');
        if ($r.length) {
            // Make sure ticket thread tab is visiable.
            var $t = $('ul#ticket_tabs > li > a#ticket-thread-tab');
            if ($t.length && !$t.hasClass('active'))
                $t.trigger('click');
            // Make the target response tab active.
            if (!$r.hasClass('active'))
                $r.trigger('click');

            // Scroll to the response section.
            var $stop = $(document).height();
            var $s = $('div#response_options');
            if ($s.length)
                $stop = $s.offset().top-125

            $('html, body').animate({scrollTop: $stop}, 'fast');
        }

        return false;
    });

  $('#show_ccs').click(function() {
    var show = $('#arrow-icon');
    var collabs = $('a#managecollabs');
    $('#ccs').slideToggle('fast', function(){
        if ($(this).is(":hidden")) {
            collabs.hide();
            show.removeClass('icon-caret-down').addClass('icon-caret-right');
        } else {
            collabs.show();
            show.removeClass('icon-caret-right').addClass('icon-caret-down');
        }
    });
    return false;
   });

  $('.collaborators.noclick').click(function() {
    $('#show_ccs').trigger('click');
   });

  $('#collabselection').select2({
    width: '350px',
    allowClear: true,
    sorter: function(data) {
        return data.filter(function (item) {
                return !item.selected;
                });
    },
    templateResult: function(e) {
        var $e = $(
        '<span><i class="icon-user"></i> ' + e.text + '</span>'
        );
        return $e;
    }
   }).on("select2:unselecting", function(e) {
        if (!confirm(__("Are you sure you want to DISABLE the collaborator?")))
            e.preventDefault();
   }).on("select2:selecting", function(e) {
        if (!confirm(__("Are you sure you want to ENABLE the collaborator?")))
             e.preventDefault();
   }).on('change', function(e) {
    var id = e.currentTarget.id;
    var count = $('li.select2-selection__choice').length;
    var total = $('#' + id +' option').length;
    $('.' + id + '__count').html(count);
    $('.' + id + '__total').html(total);
    $('.' + id + '__total').parent().toggle((total));
   }).on('select2:opening select2:closing', function(e) {
    $(this).parent().find('.select2-search__field').prop('disabled', true);
   });
});
function saveDraft() {
    redactor = $('#response').redactor('plugin.draft');
    if (redactor.opts.draftId)
        $('#response').redactor('plugin.draft.saveDraft');
}
</script>
        <link rel="stylesheet" type="text/css" href="/css/filedrop.css"/></div>
</div>
    <div id="footer">
        Derechos de autor &copy; 2006-2026&nbsp;Universidad Andina del Cusco&nbsp;Todos los derechos reservados.    </div>
    <div>
        <!-- Do not remove <img src="autocron.php" alt="" width="1" height="1" border="0" /> or your auto cron will cease to function -->
        <img src="/scp/autocron.php" alt="" width="1" height="1" border="0" />
        <!-- Do not remove <img src="autocron.php" alt="" width="1" height="1" border="0" /> or your auto cron will cease to function -->
    </div>
</div>
<div id="overlay"></div>
<div id="loading">
    <i class="icon-spinner icon-spin icon-3x pull-left icon-light"></i>
    <h1>Cargando ...</h1>
</div>
<div class="dialog draggable" style="display:none;" id="popup">
    <div id="popup-loading">
        <h1 style="margin-bottom: 20px;"><i class="icon-spinner icon-spin icon-large"></i>
        Cargando ...</h1>
    </div>
    <div class="body"></div>
</div>
<div style="display:none;" class="dialog" id="alert">
    <h3><i class="icon-warning-sign"></i> <span id="title"></span></h3>
    <a class="close" href=""><i class="icon-remove-circle"></i></a>
    <hr/>
    <div id="body" style="min-height: 20px;"></div>
    <hr style="margin-top:3em"/>
    <p class="full-width">
        <span class="buttons pull-right">
            <input type="button" value="Aceptar" class="close ok">
        </span>
     </p>
    <div class="clear"></div>
</div>

<script type="text/javascript" src="/js/jquery.pjax.js?0375576"></script>
<script type="text/javascript" src="/js/bootstrap-typeahead.js?0375576"></script>
<script type="text/javascript" src="/js/jquery-ui-1.13.2.custom.min.js?0375576"></script>
<script type="text/javascript" src="/js/jquery-ui-timepicker-addon.js?0375576"></script>
<script type="text/javascript" src="/js/jquery-ui-sliderAccess.js?0375576"></script>
<script type="text/javascript" src="/scp/js/scp.js?0375576"></script>
<script type="text/javascript" src="/js/filedrop.field.js?0375576"></script>
<script type="text/javascript" src="/js/select2.min.js?0375576"></script>
<script type="text/javascript" src="/scp/js/tips.js?0375576"></script>
<script type="text/javascript" src="/js/redactor.min.js?0375576"></script>
<script type="text/javascript" src="/js/redactor-osticket.js?0375576"></script>
<script type="text/javascript" src="/js/redactor-plugins.js?0375576"></script>
<script type="text/javascript" src="/scp/js/jquery.translatable.js?0375576"></script>
<script type="text/javascript" src="/scp/js/jquery.dropdown.js?0375576"></script>
<script type="text/javascript" src="/scp/js/bootstrap-tooltip.js?0375576"></script>
<script type="text/javascript" src="/scp/js/jb.overflow.menu.js?0375576"></script>
<link type="text/css" rel="stylesheet" href="/scp/css/tooltip.css?0375576"/>
<script type="text/javascript">
    getConfig().resolve({"lock_time":1800,"html_thread":true,"date_format":"dd\/mm\/yy","lang":"es_MX","short_lang":"es","has_rtl":false,"lang_flag":"mx","primary_lang_flag":"mx","primary_language":"es-MX","secondary_languages":[],"page_size":50,"path":"\/","editor_spacing":"double"});
</script>
</body>
</html>
