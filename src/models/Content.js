const mongoose = require('mongoose');

const contentSchema = new mongoose.Schema({
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    required: true
  },
  type: {
    type: String,
    enum: ['movie', 'series'],
    required: true
  },
  genre: [{
    type: String,
    required: true
  }],
  releaseYear: {
    type: Number,
    required: true
  },
  rating: {
    type: Number,
    min: 0,
    max: 10
  },
  duration: String,
  thumbnailUrl: String,
  videoUrl: String,
  trailerUrl: String,
  cast: [String],
  director: String,
  createdAt: {
    type: Date,
    default: Date.now
  }
});

module.exports = mongoose.model('Content', contentSchema); 