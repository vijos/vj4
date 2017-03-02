const request = {};

request.ajax = async function (options) {
  return new Promise((resolve, reject) => {
    $.ajax({
      dataType: 'json',
      ...options,
    })
    .fail((jqXHR, textStatus, errorThrown) => {
      if (textStatus === 'abort') {
        const err = new Error('aborted');
        err.aborted = true;
        reject(err);
      } if (jqXHR.readyState === 0) {
        reject(new Error('Network error'));
      } else if (errorThrown instanceof Error) {
        reject(errorThrown);
      } else if (typeof jqXHR.responseJSON === 'object' && jqXHR.responseJSON.error) {
        reject(new Error(jqXHR.responseJSON.error));
      } else {
        reject(new Error(textStatus));
      }
    })
    .done(resolve);
  });
};

request.post = function (url, dataOrForm = {}) {
  let postData;
  if (dataOrForm instanceof jQuery && dataOrForm.is('form')) {
    // $form
    postData = dataOrForm.serialize();
  } else if (dataOrForm instanceof Node && $(dataOrForm).is('form')) {
    // form
    postData = $(dataOrForm).serialize();
  } else if (typeof dataOrForm === 'string') {
    // foo=bar&box=boz
    postData = dataOrForm;
  } else {
    // {foo: 'bar'}
    postData = $.param({
      csrf_token: UiContext.csrf_token,
      ...dataOrForm,
    }, true);
  }
  return request.ajax({
    url,
    method: 'post',
    data: postData,
  });
};

request.get = function (url, qs = {}) {
  return request.ajax({
    url,
    data: qs,
    method: 'get',
  });
};

export default request;
