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

export function post(url, data = {}) {
  const postData = {
    csrf_token: UiContext.csrf_token,
    ...data,
  };
  return ajax({
    url,
    method: 'post',
    data: $.param(postData, true),
  });
}

export function get(url) {
  return ajax({
    url,
    method: 'get',
  });
}
