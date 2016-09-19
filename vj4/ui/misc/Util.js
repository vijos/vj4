export async function ajax(options) {
  try {
    const data = await $.ajax({
      dataType: 'json',
      ...options,
    });
    return data;
  } catch (resp) {
    if (resp.status === 0) {
      throw new Error('Connection failed');
    }
    if (resp.responseJSON) {
      throw new Error(resp.responseJSON.err);
    }
    throw new Error(resp.statusText);
  }
}

export function post(url, dataOrForm = {}) {
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
  return ajax({
    url,
    method: 'post',
    data: postData,
  });
}

export function get(url, qs = {}) {
  return $.ajax({
    url,
    data: qs,
    method: 'get',
  });
}
