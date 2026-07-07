export function debounce(fn, delay = 300) {
  let timer = null
  return function (...args) {
    if (timer) {
      clearTimeout(timer)
    }
    timer = setTimeout(() => {
      fn.apply(this, args)
      timer = null
    }, delay)
  }
}

export function throttle(fn, delay = 300) {
  let lastTime = 0
  let timer = null
  return function (...args) {
    const now = Date.now()
    const remaining = delay - (now - lastTime)
    
    if (remaining <= 0) {
      if (timer) {
        clearTimeout(timer)
        timer = null
      }
      lastTime = now
      fn.apply(this, args)
    } else if (!timer) {
      timer = setTimeout(() => {
        lastTime = Date.now()
        timer = null
        fn.apply(this, args)
      }, remaining)
    }
  }
}

export function withLock(fn) {
  let isLocked = false
  return async function (...args) {
    if (isLocked) {
      return
    }
    isLocked = true
    try {
      return await fn.apply(this, args)
    } finally {
      isLocked = false
    }
  }
}
