const base = import.meta.env.BASE_URL.replace(/\/$/, "");

export function publicUrl(path) {
  if (!path || /^(?:https?:)?\/\//i.test(path) || path.startsWith("data:")) return path;
  return `${base}/${path.replace(/^\//, "")}`;
}

export function absolutePublicUrl(path) {
  return new URL(publicUrl(path), window.location.origin).href;
}
