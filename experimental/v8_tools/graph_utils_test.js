'use strict';
describe('GraphUtils', function() {
  describe('getClassName', function() {
    it('should create new entries by default', function() {
      const getClassName = GraphUtils.createClassNameGenerator();
      chai.expect(getClassName('never seen')).to.equal('0');
    });
    it('should return same class name for same key', function() {
      const getClassName = GraphUtils.createClassNameGenerator();
      chai.expect(getClassName('key')).to.equal('0');
      chai.expect(getClassName('key')).to.equal('0');
    });
    it('should return different class names for different keys', function() {
      const getClassName = GraphUtils.createClassNameGenerator();
      chai.expect(getClassName('key one'))
          .to.not.equal(getClassName('key two'));
    });
  });
});
