function action(url, vmid, action, success_callback, error_callback, complete_callback) {
	$.ajax({
		url: url,
		type: 'post',
		data: {
			'vmid': vmid,
			'action': action,
		},
		success:success_callback,
		error: error_callback,
		complete:complete_callback
		
	}, 'json');
}

function update_status(url, vmids, interval){
	for(var i in vmids) {
		setInterval("get_status('"+url+"', '" + vmids[i] + "')", interval);
		get_status(url, vmids[i]);
	}
}

function get_status(url, vmid) {
	$.ajax({
		url: url,
		type: 'post',
		data: {
			'vmid': vmid,
		},
		cache:false,
		success: function(data) {
			if (data.res == true){
				if (data.status == 'deleted'){
					$("#tr_" + data.vmid).remove();
				} else {
					$("#" + window.vm_status_tag + data.vmid).html(data.status);
				}
			}
		},
	}, 'json');
}

function vm_reboot(url, vmid){
	$("#" + window.vm_task_tag + vmid).html("reboot");
	action(url, vmid, 'reboot',
		function(data){},
		function(data){},
		function(data){
			get_status(window.vm_status_url , vmid);
			$("#" + window.vm_task_tag + vmid).html("");
		}
		);
}

function vm_shutdown(url, vmid){
	$("#" + window.vm_task_tag + vmid).html("shutdown");
	action(url, vmid, 'shutdown',
		function(data){},
		function(data){},
		function(data){
			get_status(window.vm_status_url , vmid);
			$("#" + window.vm_task_tag + vmid).html("");}
		);
}

function vm_poweroff(url, vmid){
	$("#" + window.vm_task_tag + vmid).html("poweroff");
	action(url, vmid, 'poweroff',
		function(data){},
		function(data){},
		function(data){
			get_status(window.vm_status_url , vmid);
			$("#" + window.vm_task_tag + vmid).html("");}
		);
}

function vm_start(url, vmid){
	$("#" + window.vm_task_tag + vmid).html("start");
	action(url, vmid, 'start',
		function(data){},
		function(data){},
		function(data){
			get_status(window.vm_status_url , vmid);
			$("#" + window.vm_task_tag + vmid).html("");}
		);
}

function vm_delete(url, vmid){
	if(!confirm('You are deleting a VM, are you sure?'))
		return;
	$("#" + window.vm_task_tag + vmid).html("delete");
	action(url, vmid, 'delete',
		function(data){},
		function(data){},
		function(data){
			get_status(window.vm_status_url , vmid);
			$("#" + window.vm_task_tag + vmid).html("");}
		);
}