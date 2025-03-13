const express = require('express');
const router = express.Router();
const User = require('../models/User');
const auth = require('../middleware/auth');
const { check } = require('express-validator');
const validate = require('../middleware/validate');

// Get user profile
router.get('/profile', auth, async (req, res) => {
  try {
    const user = await User.findById(req.user.id)
      .select('-password')
      .populate('myList');
    
    res.json({
      status: 'success',
      data: user
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({
      status: 'error',
      message: 'Server error'
    });
  }
});

// Update watch history
router.post('/history', auth, async (req, res) => {
  try {
    const { contentId, progress } = req.body;
    
    await User.findByIdAndUpdate(req.user.id, {
      $push: {
        watchHistory: {
          content: contentId,
          progress,
          watchedAt: new Date()
        }
      }
    });

    res.json({
      status: 'success',
      message: 'Watch history updated'
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({
      status: 'error',
      message: 'Server error'
    });
  }
});