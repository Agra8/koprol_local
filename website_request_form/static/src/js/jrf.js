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
	var table = document.getElementById(value);
	var row = table.insertRow();
	var index = document.getElementById('request_tbl').children[1].children.length;
	console.log(index);
	if (value == 'request_tbl') {
		row.innerHTML = `        <tr>
                                          <td class="td-custom">
                                            <table class="table responsive text-center" >
                                              <tr>
                                                <th scope="col">Type Request</th>
                                                <th scope="col">Request</th>
                                              </tr>
                                              <tr>
                                                <td>
													<select id="requestform_id_${index}" name="requestform_id" class="form-control s_website_form_input input-types" placeholder="" required="true">
														<option value="">(Silahkan Pilih)</option>
														<option value="arf">Access Request</option>
														<option value="jrf">Job Request</option>
													</select>
                                              	</td>
                                              <td>
												<select id="request_id_${index}" name="request_line_ids" class="form-control s_website_form_input" placeholder="" required="true">
													<option value="">(Silahkan Pilih)</option>
												</select>
                                              </td>
                                              </tr>
                                              <tr> 
                                              <td class="td-custom" colspan="2">
                                                <textarea class="text-area form-control s_website_form_input s_website_form_model_required" name="request_line_keterangan[]" placeholder="Keterangan" required="true"></textarea>
                                              </td>
                                              </tr>
											   <tr>
                                                    <td>
                                                      <div class="form-group row form-field s_website_form_custom">
                                                        <div class="col-lg-3 col-md-4 text-left">
                                                            <label class="col-form-label" for="Scan Ijazah Terakhir">Lampiran</label>
                                                        </div>
                                                        <div class="col-lg-7 col-md-8">
                                                            <input type="file" class="form-control s_website_form_input" name="attachment" required=""/>
                                                        </div>
                                                        </div>
                                                    </td>
                                                  </tr>
                                            </table>
                                          </td>
                                              <td class="td-custom" style="width:6%;">
												<button type="button" class="btn custom-btn-primary rounded-circle buttonx" style="font-size: 0.75rem;" onclick="deleteRow(this.parentElement.parentElement)">X</button>
											  </td>
                                        </tr>
					`;
		document.getElementById(value).insertRow(row);
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
