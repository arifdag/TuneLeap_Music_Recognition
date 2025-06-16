import 'package:flutter/material.dart';

class LoginPromptDialog extends StatelessWidget {
  final VoidCallback? onLoginPressed;

  const LoginPromptDialog({Key? key, this.onLoginPressed}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('Login Required'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('You need to be logged in to use this feature.'),
          SizedBox(height: 12),
          Text(
            'Login to save recognized songs to your history and access them later.',
            style: TextStyle(fontSize: 14, color: Colors.grey[600]),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context, false),
          child: Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: () {
            Navigator.pop(context, true);
            if (onLoginPressed != null) {
              onLoginPressed!();
            }
          },
          child: Text('Login'),
        ),
      ],
    );
  }

  static Future<bool> show(BuildContext context, {VoidCallback? onLoginPressed}) async {
    final result = await showDialog<bool>(
      context: context,
      builder: (context) => LoginPromptDialog(
        onLoginPressed: onLoginPressed ?? () {
          // Default navigation to login screen if no custom handler provided
          Navigator.of(context).pushNamed('/login');
        },
      ),
    );
    return result ?? false;
  }
} 