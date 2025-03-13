const express = require('express');
const router = express.Router();
const Content = require('../models/Content');
const auth = require('../middleware/auth');
const { check } = require('express-validator');
const validate = require('../middleware/validate');
const User = require('../models/User');

// Get all content with pagination and filters
router.get('/', auth, async (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 10;
    const genre = req.query.genre;
    const type = req.query.type;
    const search = req.query.search;

    const query = {};
    if (genre) query.genre = genre;
    if (type) query.type = type;
    if (search) {
      query.$or = [
        { title: { $regex: search, $options: 'i' } },
        { description: { $regex: search, $options: 'i' } }
      ];
    }

    const total = await Content.countDocuments(query);
    const content = await Content.find(query)
      .sort({ createdAt: -1 })
      .skip((page - 1) * limit)
      .limit(limit);

    res.json({
      status: 'success',
      data: {
        content,
        pagination: {
          page,
          limit,
          total,
          pages: Math.ceil(total / limit)
        }
      }
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({
      status: 'error',
      message: 'Server error'
    });
  }
});

// Get content by ID
router.get('/:id', auth, async (req, res) => {
  try {
    const content = await Content.findById(req.params.id);
    if (!content) {
      return res.status(404).json({ message: 'Content not found' });
    }
    res.json(content);
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server error');
  }
});

// Get content by genre
router.get('/genre/:genre', auth, async (req, res) => {
  try {
    const content = await Content.find({ genre: req.params.genre });
    res.json(content);
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server error');
  }
});

// Add content recommendation endpoint
router.get('/recommendations', auth, async (req, res) => {
  try {
    const userPreferences = await User.findById(req.user.id).select('myList');
    const userGenres = await Content.distinct('genre', {
      _id: { $in: userPreferences.myList }
    });

    const recommendations = await Content.find({
      genre: { $in: userGenres },
      _id: { $nin: userPreferences.myList }
    })
    .limit(10);

    res.json({
      status: 'success',
      data: recommendations
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({
      status: 'error',
      message: 'Server error'
    });
  }
});

module.exports = router; 