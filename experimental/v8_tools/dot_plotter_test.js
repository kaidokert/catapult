'use strict';
const getStackedOffsets = (data) => {
  const dotPlotter = new DotPlotter();
  // Stubs the x axis scale so that theres a 1:1 mapping between pixel
  // values and memory values.
  const scale = {
    invert: x => x,
  };
  const stackedLocations = dotPlotter.computeDotStacking_(data.source, scale);
  return stackedLocations.map(({x, stackOffset}) => stackOffset);
};
describe('DotPlotter', function() {
  describe('dot stacking', function() {
    it('should not stack far away values', function() {
      const data = {
        source: [5, 40, 90, 100],
      };
      const stackedOffsets = getStackedOffsets(data);
      chai.expect(stackedOffsets).to.eql([0, 0, 0, 0]);
    });
    it('should stack duplicates', function() {
      const data = {
        source: [100, 100, 100],
      };
      const stackedOffsets = getStackedOffsets(data);
      chai.expect(stackedOffsets).to.have.members([-1, 0, 1]);
    });
    it('should allow for multiple stacks', function() {
      const data = {
        source: [992, 994, 555, 556, 15],
      };
      const stackedOffsets = getStackedOffsets(data);
      chai.expect(stackedOffsets).to.have.members([-1, 0, -1, 0, 0]);
    });
  });
  describe('plotting', function() {
    const graph = new GraphData();
    it('should plot data despite invalid selection characters', function() {
      const data = {
        'source.with:inv@lid _chars"}~$': [1, 2, 3, 4, 5],
      };
      graph.setData(data);
      chai.expect(() => graph.plotDot()).to.not.throw(Error);
      chai.expect(
          document.querySelectorAll('.dot-0').length)
          .to.equal(5);
    });
    it('should trigger the supplied callback when a dot is clicked',
        function() {
          const data = {
            'label': [1],
          };
          const receivedArguments = [];
          const callback = (metric, story, key, index) => {
            receivedArguments.push(key);
            receivedArguments.push(index);
          };
          graph.setData(data, callback).plotDot();
          d3.selectAll('circle').dispatch('click');
          chai.expect(receivedArguments.length).to.equal(2);
          chai.expect(receivedArguments[0]).to.equal('label');
          chai.expect(receivedArguments[1]).to.equal(0);
        });
    it('should trigger the supplied callback when a dot is clicked',
        function() {
          const data = {
            'labelOne': [5, 8, 10],
            'labelTwo': [4, 1],
          };
          let receivedArguments = [];
          const callback = (metric, story, key, index) => {
            receivedArguments.push(key);
            receivedArguments.push(index);
          };
          const checkReceivedArgs = (expectedLabel, expectedIndex) => {
            chai.expect(receivedArguments.length).to.equal(2);
            chai.expect(receivedArguments[0]).to.equal(expectedLabel);
            chai.expect(receivedArguments[1]).to.equal(expectedIndex);
            receivedArguments = [];
          };
          graph.setData(data, callback).plotDot();
          d3.select('.chai-test-dot-0-5').dispatch('click');
          checkReceivedArgs('labelOne', 0);
          d3.select('.chai-test-dot-0-8').dispatch('click');
          checkReceivedArgs('labelOne', 1);
          d3.select('.chai-test-dot-0-10').dispatch('click');
          checkReceivedArgs('labelOne', 2);
          d3.select('.chai-test-dot-1-4').dispatch('click');
          checkReceivedArgs('labelTwo', 0);
          d3.select('.chai-test-dot-1-1').dispatch('click');
          checkReceivedArgs('labelTwo', 1);
        });
  });
});
