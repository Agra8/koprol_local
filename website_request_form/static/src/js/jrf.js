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
			'afterend',
			`        				<div>
									<div class="w3-row">
                                      <label class="w3-col m1 s_website_form_label" style="width: 200px" for="2hvgthz7mmr">
                                        <span class="s_website_form_label_content">Request</span>
                                        <span class="s_website_form_mark"> *</span>
                                      </label>
                                      <button type="button" class="btn custom-btn-primary rounded-circle buttonx custom-btn-close" style="font-size: 0.75rem;" onclick="deleteRow(this.parentElement.parentElement)">X</button>
                                      <div class="w3-col m1 w3-center w3-container m4 l3">
                                        <select id="requestform_id_${index +
											1}" name="requestform_id" class="form-control s_website_form_input input-types"  placeholder="" required="true">
                                           <option value="">Pilih Tipe Request</option>
                                           <option value="arf">Access Request</option>
                                           <option value="jrf">Job Request</option>
                                        </select>
                                      </div>
                                      <div class="w3-col m1 w3-center w3-container m4 l6 custom-row">
                                        <select id="request_id_${index +
											1}" name="request_line_ids" class="form-control s_website_form_input" placeholder="" required="true">
                                           <option value="">(Silahkan Pilih)</option>
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
                                    <div class="form-group s_website_form_field col-12 s_website_form_custom" data-name="Field" style="padding-top: 15px;">
                                      <div class="row s_col_no_resize s_col_no_bgcolor">
                                        <label class="col-form-label col-sm-auto s_website_form_label" style="width: 200px" for="imwez0wfsx">
                                          <span class="s_website_form_label_content">Lampiran</span>
                                          <span class="s_website_form_mark"> </span>
                                        </label>
                                        <div class="col-sm">
                                          <input type="file" class="form-control s_website_form_input" name="attachment" required=""/>
                                        </div>
                                      </div>
                                    </div>
									</div>
					`
		);
		initEvent();
		tbl('#request_tbl', 'keyup', "input[name='requestform_id']");
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

$(document).on('change', '.input-types', function() {
	idRequest = this.id.split('_');
	otherSelector = 'select[id="request_id_' + idRequest[2] + '"]';
	valueRequest = this.value;
	request = document.getElementById('requestjrf_').children;
	requestForm = document.querySelector(otherSelector);
	requestForm.innerHTML = '';
	requestFormOption = ``;

	if (this.value != '') {
		var opt = document.createElement('option');
		opt.innerHTML = '(Silahkan Pilih)';
		requestForm.appendChild(opt);
	}

	[].forEach.call(request, function(el) {
		var temp = el.value.split('-');
		if (temp[0] == valueRequest) {
			var opt = document.createElement('option');
			opt.value = temp[1];
			opt.innerHTML = el.innerText;
			requestForm.appendChild(opt);
		}
	});

	initEvent();
});

$(document).on('change', '.input-company', function() {
	otherSelector = 'select[id="branch"]';
	valueRequest = this.value;
	console.log(otherSelector);
	request = document.getElementById('branchdropdown').children;
	requestForm = document.querySelector(otherSelector);
	requestForm.innerHTML = '';
	requestFormOption = ``;

	if (this.value != '') {
		var opt = document.createElement('option');
		opt.innerHTML = '(Silahkan Pilih)';
		requestForm.appendChild(opt);
	}

	[].forEach.call(request, function(el) {
		var temp = el.value.split('-');
		if (temp[0] == valueRequest) {
			var opt = document.createElement('option');
			opt.value = temp[1];
			opt.innerHTML = el.innerText;
			requestForm.appendChild(opt);
		}
	});

	initEvent();
});

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
}

// function functionDebug() {
// 	// document.querySelector('#main_form').addEventListener('submit', (e) => {
// 	// e.preventDefault();
// 	var forms = document.querySelectorAll('form');
// 	console.log(forms);
// 	var jrfLines = [];
// 	[ ...forms ].forEach((form) => {
// 		var formsVals = {};
// 		[ ...document.querySelectorAll(`[form='${form.id}']`) ].forEach((field) => {
// 			formsVals[field.name] = field.value;
// 		});
// 		console.log(formsVals);
// 		jrfLines.push(formsVals);
// 	});
// 	console.log(jrfLines);
// }
