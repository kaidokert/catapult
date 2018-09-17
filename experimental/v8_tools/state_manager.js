'use strict';
class StateManager {
  constructor() {
    this.history_ = [];
    this.current_ = undefined;
  }

  pushState(state) {
    if (this.current_ !== undefined) {
      this.history_.push(this.current_);
    }
    this.current_ = state;
  }

  popState() {
    this.current_ = this.history_.pop() || undefined;
    return this.current_;
  }
}
