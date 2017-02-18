const request = {};

request.ajax = async function (options, dataType = 'json') {
  try {
    const data = await $.ajax({
      dataType,
      ...options,
    });
    return data;
  } catch (resp) {
    if (resp.status === 0) {
      throw new Error('Connection failed');
    }
    if (resp.responseJSON) {
      throw resp.responseJSON.error;
    }
    throw new Error(resp.statusText);
  }
};

request.post = function (url, dataOrForm = {}, dataType = 'json') {
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
  }, dataType);
};

request.get = function (url, qs = {}, dataType = 'json') {
  return request.ajax({
    url,
    data: qs,
    method: 'get',
  }, dataType);
};

export default request;
