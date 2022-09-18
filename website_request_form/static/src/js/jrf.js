if (document.readyState !== 'loading') {
	initEvent();
} else {
	document.addEventListener('DOMContentLoaded', function() {
		initEvent();
	});
}

$(document).ready(function() {
	$('.select_field').select2();
});

$(document).ready(function() {
	$('#branchdropdown').select2();
});

function initEvent() {
	tbl('#request_tbl', 'keyup', "input[name='requestform_id']");
}

function addRow(value) {
	var newDiv = document.getElementById(value);
	var index = document.querySelectorAll('.w3-row').length;
	console.log(newDiv);
	if (value == 'request_tbl') {
		newDiv.insertAdjacentHTML(
			'beforeend',
			`        				<div>
			 						<div class="s_hr text-left pt32 pb18" data-snippet="s_hr" data-name="Separator">
                                        <hr class="w-100 mx-auto" style="border-top-style: double !important; border-top-width: 5px !important; margin-bottom: 25px;"/>
                                    </div>
									<p name="number" style="text-align:left;  font-weight: bold;"></p>
									<div class="w3-row">
                                      <label class="w3-col m1 s_website_form_label" style="width: 200px" for="2hvgthz7mmr">
                                        <span class="s_website_form_label_content">Request</span>
                                        <span class="s_website_form_mark"> *</span>
                                      </label>
                                      <button type="button" class="btn custom-btn-primary rounded-circle buttonx custom-btn-close" style="font-size: 0.75rem;" onclick="deleteRow(this.parentElement.parentElement)">X</button>
                                      <div class="w3-col m1 w3-center w3-container m4 l3">
                                        <select id="requestform_id_${index +
											1}" name="request_line_ids" class="form-control select_field_${index + 1} s_website_form_input input-types"  placeholder="" required="true">
                                           <option value="">Pilih Tipe Request</option>
                                        </select>
                                      </div>
                                      <div class="w3-col m1 w3-center w3-container m4 l6 custom-row">
                                        <select id="request_id_${index +
											1}"  name="request_sistem_ids" class="form-control select_field_${index + 1} s_website_form_input" placeholder="" required="true">
                                          <option value="">(Silahkan Pilih)</option>
                                          <t t-foreach="tipe_sistem" t-as="tipe_sistem">
                                              <option t-attf-value="#{tipe_sistem.id}">
                                                  <t t-esc="tipe_sistem.name"/> -
                                                  <t t-esc="tipe_sistem.company_id.name"/>
                                              </option>
                                          </t>
                                        </select>
                                      </div>
                                    </div>
                                    <div class="form-group s_website_form_field col-12 s_website_form_custom s_website_form_required" data-name="Field" style="padding-top: 15px;">
                                      <div class="row s_col_no_resize s_col_no_bgcolor">
                                        <label class="col-form-label col-sm-auto s_website_form_label" style="width: 200px" for="imwez0wfsx">
                                          <span class="s_website_form_label_content"></span>
                                          <span class="s_website_form_mark"> </span>
                                        </label>
                                        <div class="col-sm">
                                          <textarea class="text-area form-control s_website_form_input s_website_form_model_required" name="request_line_keterangan[]" placeholder="Keterangan" required="1"></textarea>
                                        </div>
                                      </div>
                                    </div>
                                  <div class="form-group s_website_form_field s_website_form_custom" data-name="Field" style="padding-top: 15px;">
                                      <div class="row s_col_no_resize s_col_no_bgcolor">
                                        <label class="col-form-label col-sm-auto s_website_form_label" style="width: 200px" for="imwez0wfsx">
                                          <span class="s_website_form_label_content">Lampiran</span>
                                          <span class="s_website_form_mark"> </span>
                                        </label>
                                        <div class="col-sm-8" style="padding-left: 30px;">
                                          <input type="file" class="form-control s_website_form_input" name="attachment"/>
                                        </div>
                                      </div>
                                    </div>
									</div>
					`
		);
		initEvent();
		changeAddRequest();
		tbl('#request_tbl', 'keyup', "input[name='requestform_id']");
		numberRow();
	}
}

function tbl(selector, eventType, childSelector) {
	var elements = document.querySelectorAll("input[type='text']", selector);
	for (element of elements) {
		element.addEventListener(eventType, (eventOnElement) => {
			if (eventOnElement.target.matches(childSelector)) {
				eventOnElement.target.value = eventOnElement.target.value.replace(/[\W]/g, '_');
				// eventHandler(eventOnElement)
			}
		});
	}
}

function changeByCompany() {
	otherSelector = 'select[id="branch"]';
	otherSelectorDepartment = 'select[id="department"]';
	var index = document.querySelectorAll('.w3-row').length;
	console.log(otherSelector);
	request = document.getElementById('branchdropdown').children;
	requestDepartment = document.getElementById('departmentdropdown').children;
	request_tipe = document.getElementById('requestform_id').children;
	company_id = document.getElementById('imwez0wfsx').selectedOptions[0].value;
	requestForm = document.querySelector(otherSelector);
	requestFormDepartment = document.querySelector(otherSelectorDepartment);
	requestForm.innerHTML = '';
	requestFormDepartment.innerHTML = '';
	requestFormOption = ``;
	requestFormOptionDepartment = ``;

	for (let i = 0; i < index; i++) {
		selectorTipeFormId = document.querySelectorAll('.w3-row')[i].childNodes[5].childNodes[1].id;
		selectorTipeForm = `select[id="${selectorTipeFormId}"]`;
		requestTipeForm = document.querySelector(selectorTipeForm);
		requestTipeForm.innerHTML = '';

		if (this.value != '') {
			var opts = document.createElement('option');
			opts.value = 'NULL';
			opts.innerHTML = '(Pilih Tipe Request)';
			requestTipeForm.appendChild(opts);
		}

		[].forEach.call(request_tipe, function(e) {
			var temporaryTipe = e.value.split('-');
			if (temporaryTipe[2] == company_id || temporaryTipe[2] == '') {
				var options = document.createElement('option');
				options.value = `${temporaryTipe[0]}-${temporaryTipe[1]}`;
				options.innerHTML = e.innerText;
				requestTipeForm.appendChild(options);
			}
		});
		requestId = document.querySelectorAll('.w3-row')[i].childNodes[7].childNodes[1].id;
		document.getElementById(requestId).style.display = 'none';
		// document.getElementById(`request_id_${i}`).disabled = true;
		// document.getElementById(`request_id_${i}`).value = 'XXX';

		$(requestId).prop('selectedIndex', 0);
	}

	if (this.value != '') {
		var opt = document.createElement('option');
		opt.value = 'NULL';
		opt.innerHTML = '(Silahkan Pilih)';
		requestForm.appendChild(opt);
	}

	[].forEach.call(request, function(el) {
		var temp = el.value.split('-');
		if (temp[0] == company_id) {
			var opt = document.createElement('option');
			opt.value = temp[1];
			opt.innerHTML = el.innerText;
			requestForm.appendChild(opt);
		}
	});
	if (this.value != '') {
		var opt = document.createElement('option');
		opt.value = 'NULL';
		opt.innerHTML = '(Silahkan Pilih)';
		requestFormDepartment.appendChild(opt);
	}

	[].forEach.call(requestDepartment, function(el) {
		var temp = el.value.split('-');
		if (temp[0] == company_id) {
			var opt = document.createElement('option');
			opt.value = temp[1];
			opt.innerHTML = el.innerText;
			requestFormDepartment.appendChild(opt);
		}
	});

	initEvent();
}

function changeAddRequest() {
	var index = document.querySelectorAll('.w3-row').length;
	selectorTipeForm = `select[id="requestform_id_${index}"]`;
	request_tipe = document.getElementById('requestform_id').children;
	company_id = document.getElementById('imwez0wfsx').selectedOptions[0].value;
	requestTipeForm = document.querySelector(selectorTipeForm);
	requestTipeForm.innerHTML = '';

	if (this.value != '') {
		var opts = document.createElement('option');
		opts.value = 'NULL';
		opts.innerHTML = '(Pilih Tipe Request)';
		requestTipeForm.appendChild(opts);
	}

	[].forEach.call(request_tipe, function(e) {
		var temporaryTipe = e.value.split('-');
		if (temporaryTipe[2] == company_id || temporaryTipe[2] == '') {
			var options = document.createElement('option');
			options.value = `${temporaryTipe[0]}-${temporaryTipe[1]}`;
			options.innerHTML = e.innerText;
			requestTipeForm.appendChild(options);
		}
	});

	// document.getElementById(`request_id_${index}`).disabled = true;
	document.getElementById(`request_id_${index}`).style.display = 'none';
	$(`#request_id_${index}`).prop('selectedIndex', 0);

}

$(document).on('change', '.input-types', function() {
	idRequest = this.id.split('_');
	company_id = document.getElementById('imwez0wfsx').selectedOptions[0].value;
	requestTipeSistem = document.getElementById('tipe_sistem').children;
	valueRequest = this.value.split('-');
	selectorTipeSistem = `select[id="request_id_${idRequest[2]}"]`;
	requestTipeSistemForm = document.querySelector(selectorTipeSistem);
	requestTipeSistemForm.innerHTML = '';

	if (this.value != '') {
		var opt = document.createElement('option');
		opt.value = 'NULL';
		opt.innerHTML = '(Silahkan Pilih)';
		requestTipeSistemForm.appendChild(opt);
	}

	[].forEach.call(requestTipeSistem, function(e) {
		var temporaryTipe = e.value.split('-');
		var options = document.createElement('option');
		options.value = temporaryTipe[0];
		options.innerHTML = e.innerText;
		requestTipeSistemForm.appendChild(options);
	});

	document.getElementById(`request_id_${idRequest[2]}`).style.display = 'none';
	// document.getElementById(`request_id_${idRequest[2]}`).disabled = true;
	$(`#request_id_${idRequest[2]}`).prop('selectedIndex', 0);
	if (valueRequest[1] == 'Sistem') {
		// document.getElementById(`request_id_${idRequest[2]}`).disabled = false;
		document.getElementById(`request_id_${idRequest[2]}`).style.display = 'block';
	}
});

// document.getElementById('main_form').addEventListener('keyup', function(event) {
// 	$('input, select').prop('disabled', false);
// });
// $(document).ready(function() {
// 	$('#main_form').submit(function() {
// 		$('input, select').prop('disabled', false);
// 	});
// });
function showSearch() {
	var x = document.getElementById('section_search');
	if (x.style.display === 'none') {
		x.style.display = 'block';
	} else {
		x.style.display = 'none';
	}
}

function deleteRow(value) {
	value.remove();
	numberRow();
}

function numberRow() {
	let numberRange = document.querySelectorAll('.w3-row').length;
	let number = 0;
	let numberInnerHtml = 2;
	let name = document.getElementsByName('number');
	for (numberInnerHtml; numberInnerHtml <= numberRange; numberInnerHtml++) {
		name[number].innerText = 'Nomor: ' + numberInnerHtml;
		number++;
	}
}

// ? Function auto fill form request

function searchNik() {
	
	// data ini diambil dari
	const nik = document.getElementById("search_nik").value
	const data = { nik: nik };
	const url = location.origin
	
	// TOOD: setelah mendapatkan data masukan semua value dari data tersebut ke field field
	fetch(`${url}/get_profile`, {
	  method: 'POST', 
	  headers: {
		'Content-Type': 'application/json',
	  },
	  body: JSON.stringify(data),
	})
	  .then((response) => response.json())
	  .then((data) => {
			if ( data['result'][0] == 400) {
				document.getElementById("info_search").innerHTML = data['result'][1];
				document.getElementById("info_search").style.display = "block";
			} 
			else {
				// Company ID
				changeCompanyByAutoFill(data['result'][1]["company_id"])
				// Branch ID
				changeBranchByAutoFill(data['result'][1]["branch_id"])
				// Department ID
				changeDepartmentByAutoFill(data['result'][1]["department_id"])
				// Job ID
				changeJobByAutoFill(data['result'][1]["job_id"])
				// name
				document.getElementById("7b7qknsi30q").value = data['result'][1]["name"]
				// NIK
				document.getElementById("2hvgthz7mmr").value = data['result'][1]["nik"]
				// Email
				document.getElementById("8kk85gkl467").value = data['result'][1]["email"]

			}
			console.log('Success:', data);
			return false;
	  })
	  .catch((error) => {
		  console.error('Error:', error);
		  return false;
	  });
	
	return false;
}
function changeCompanyByAutoFill(company_id){
	$(document).ready(function(){
		  const value = company_id
		  $('#imwez0wfsx').val(value).trigger("change");
		  text = $('#imwez0wfsx option:selected').text()
		  let result = text.replace(/^\s+|\s+$/gm,'');
		  document.getElementById("select2-imwez0wfsx-container").innerHTML = result
		});
}
function changeBranchByAutoFill(branch_id){
	$(document).ready(function(){
		  const value = branch_id
		  $('#branch').val(value).trigger("change");
		  text = $('#branch option:selected').text()
		  let result = text.replace(/^\s+|\s+$/gm,'');
		  document.getElementById("select2-branch-container").innerHTML = result
		});
}

function changeDepartmentByAutoFill(department_id){
	$(document).ready(function(){
		  const value = department_id
		  $('#department').val(value).trigger("change");
		  text = $('#department option:selected').text()
		  let result = text.replace(/^\s+|\s+$/gm,'');
		  document.getElementById("select2-department-container").innerHTML = result
		});
}
function changeJobByAutoFill(job_id){
	$(document).ready(function(){
		  const value = job_id
		  $('#imwez0wfsxb').val(value).trigger("change");
		  text = $('#imwez0wfsxb option:selected').text()
		  let result = text.replace(/^\s+|\s+$/gm,'');
		  document.getElementById("select2-imwez0wfsxb-container").innerHTML = result
		});
}