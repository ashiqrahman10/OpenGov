import React from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from "@/components/ui/label"

const page = () => {
  return (
    <div>
      <div>
        <h1>Report an Issue</h1>
        <p>Submit your thoughts on anything related to your government</p>
      </div>
      <div>
        <Label htmlFor="issue">Enter your issue</Label>
        <Input id='issue' />
      </div>
    </div>
  )
}

export default page