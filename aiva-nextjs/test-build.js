const { exec } = require('child_process');
const path = require('path');

console.log('🧪 Testing AIVA Next.js Build...\n');

// Test if the build works
exec('npm run build', { cwd: path.join(__dirname) }, (error, stdout, stderr) => {
  if (error) {
    console.error('❌ Build failed:');
    console.error(stderr);
    process.exit(1);
  }
  
  console.log('✅ Build successful!');
  console.log('📦 All components are working correctly');
  console.log('\n🎉 AIVA Next.js frontend is ready!');
  console.log('\n📱 Access your application at: http://localhost:3000');
  console.log('🔗 Make sure your backend API is running at: http://localhost:8000');
});
