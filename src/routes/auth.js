const express = require('express');
const router = express.Router();
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { check } = require('express-validator');
const User = require('../models/User');
const auth = require('../middleware/auth');
const validate = require('../middleware/validate');

// Validation rules
const registerValidation = [
  check('email', 'Please include a valid email').isEmail(),
  check('password', 'Password must be 6 or more characters').isLength({ min: 6 }),
  check('profileName', 'Profile name is required').not().isEmpty()
];

const loginValidation = [
  check('email', 'Please include a valid email').isEmail(),
  check('password', 'Password is required').exists()
];

// Register user
router.post('/register', registerValidation, validate, async (req, res) => {
  try {
    const { email, password, profileName } = req.body;

    let user = await User.findOne({ email });
    if (user) {
      return res.status(400).json({
        status: 'error',
        message: 'User already exists'
      });
    }

    user = new User({
      email: email.toLowerCase(),
      password,
      profileName
    });

    const salt = await bcrypt.genSalt(12);
    user.password = await bcrypt.hash(password, salt);

    await user.save();

    const payload = {
      user: {
        id: user.id
      }
    };

    const token = jwt.sign(payload, process.env.JWT_SECRET, { expiresIn: '24h' });
    
    res.status(201).json({
      status: 'success',
      data: {
        token,
        user: {
          id: user.id,
          email: user.email,
          profileName: user.profileName
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

// Add refresh token functionality
router.post('/refresh-token', auth, async (req, res) => {
  try {
    const user = await User.findById(req.user.id).select('-password');
    const payload = {
      user: {
        id: user.id
      }
    };
    
    const token = jwt.sign(payload, process.env.JWT_SECRET, { expiresIn: '24h' });
    
    res.json({
      status: 'success',
      data: { token }
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({
      status: 'error',
      message: 'Server error'
    });
  }
}); 